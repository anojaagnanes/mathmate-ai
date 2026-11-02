'use client';
import { Component, Suspense, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { Box3, Group, Matrix4, MathUtils, Mesh, MeshStandardMaterial, SkinnedMesh, Object3D, Quaternion, Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone } from 'three/addons/utils/SkeletonUtils.js';
import { gestureAt, type Gesture } from '@/lib/teacher-performance';
import { visemes, type LipSyncClock, type SyncMode } from '@/lib/lip-sync';
import type {WritingBoardState} from './writing-board-scene';
import type { TeacherState } from '@/lib/teacher-state';

class SceneBoundary extends Component<{children: ReactNode}, {failed: boolean}> {
  state = {failed: false};
  static getDerivedStateFromError() {return {failed: true};}
  render() {return this.state.failed ? <p className="avatar-fallback" role="alert">Mia’s 3D model could not load. You can still use the lesson, voice and captions. Reload to retry.</p> : this.props.children;}
}

// Keep Mia's fingertip just off the glyph so her hand never covers the letters.
const HAND_SIDE_OFFSET = .09;
const HAND_LIFT_OFFSET = -.06;

// Mia renders with the original rigged Rocketbox model (teacher.glb) via the Human path below.
type PerformanceProps = {state: TeacherState; speech: LipSyncClock; syncMode: SyncMode; stepNumber?: number; teachingGesture?: "point"; writingBoard?: WritingBoardState};
function Human({state, speech, stepNumber, teachingGesture, writingBoard, reduced, ready, onGesture}: PerformanceProps & {reduced: boolean; ready: () => void; onGesture: (gesture: Gesture) => void}) {
  const gltf = useLoader(GLTFLoader, '/models/mia/teacher.glb');

  const root = useRef<Group>(null);
  const rig = useMemo(() => {
    const scene = clone(gltf.scene);
    scene.updateMatrixWorld(true);
    scene.traverse(o => {if (o instanceof SkinnedMesh) {o.skeleton.update(); o.computeBoundingBox();}});
    const bounds = new Box3().setFromObject(scene, true);
    const height = bounds.max.y - bounds.min.y;
    const scale = 1.7 / height;
    const meshes: Mesh[] = [];
    const materials: MeshStandardMaterial[] = [];

    scene.traverse(o => {if (o instanceof Mesh) {
      o.frustumCulled=false;
      if (o.morphTargetDictionary) meshes.push(o);
      const prepare = (m: MeshStandardMaterial) => {const copy = m.clone(); copy.metalness = 0; if (copy.name.includes('head')) copy.normalScale.setScalar(.65); materials.push(copy); return copy;};
      o.material = Array.isArray(o.material) ? o.material.map(prepare) : prepare(o.material);
    }});
    const bones = new Map<string, {node: Object3D; rest: Quaternion}>();
    const boneNames = ['Head', 'Neck', 'Spine2', 'LeftArm', 'RightArm', 'LeftForeArm', 'RightForeArm', 'LeftHand', 'RightHand'];
    for (const side of ['Left','Right']) for (const finger of ['Thumb','Index','Middle','Ring','Pinky']) for (const joint of [1,2,3]) boneNames.push(`${side}Hand${finger}${joint}`);
    for (const name of boneNames) {
      const node = scene.getObjectByName(name);
      if (node) bones.set(name, {node, rest: node.quaternion.clone()});
    }
    return {scene, scale, y: -bounds.min.y * scale, meshes, bones, materials};
  }, [gltf]);
  useEffect(ready, [ready]);
  useEffect(() => () => {rig.materials.forEach(m => m.dispose()); rig.scene.traverse(o => {if (o instanceof SkinnedMesh) o.skeleton.dispose();});}, [rig]);
  const offset = useMemo(() => new Quaternion(), []);
  const pose = useMemo(() => new Quaternion(), []);
  const lastGesture = useRef<Gesture>('rest');
  const event = useRef({state, stepNumber, age:0});
  const axis = useMemo(() => new Vector3(), []);
  function bone(name: string, x: number, y: number, z: number, dt: number) {
    const b = rig.bones.get(name); if (!b) return;
    pose.copy(b.rest);
    for (const [a, angle] of [[0,x],[1,y],[2,z]]) {
      axis.set(a === 0 ? 1 : 0, a === 1 ? 1 : 0, a === 2 ? 1 : 0);
      pose.multiply(offset.setFromAxisAngle(axis, angle));
    }
    b.node.quaternion.slerp(pose, 1 - Math.exp(-5 * Math.min(dt,.1)));
  }
  const handBasis = useMemo(() => ({x:new Vector3(),y:new Vector3(),z:new Vector3(),matrix:new Matrix4(),parent:new Quaternion(),target:new Quaternion()}),[]);
  function orientHand(side: string, kind: string, dt: number) {
    const b=rig.bones.get(`${side}Hand`);if(!b?.node.parent)return;
    const sign=side==='Left'?1:-1;
    const h=handBasis;
    h.y.set(kind==='point'?-.9:kind==='open'||kind==='reassure'?sign*.3:0,kind==='open'||kind==='reassure'?.15:1,kind==='open'||kind==='reassure'?.9:.15).normalize();
    h.z.set(0,kind==='open'||kind==='reassure'?sign:0,kind==='open'||kind==='reassure'?0:sign);
    h.z.addScaledVector(h.y,-h.z.dot(h.y)).normalize();h.x.crossVectors(h.y,h.z).normalize();
    h.target.setFromRotationMatrix(h.matrix.makeBasis(h.x,h.y,h.z));
    b.node.parent.getWorldQuaternion(h.parent).invert();h.target.premultiply(h.parent);
    // Keep the wrist within a comfortable range of this model's authored pose.
    // Unconstrained world-facing palms produced severe wrist twists on this rig.
    const angle=b.rest.angleTo(h.target);
    pose.copy(h.target);
    h.target.copy(b.rest).slerp(pose,Math.min(1,.7/Math.max(.001,angle)));
    b.node.quaternion.slerp(h.target,1-Math.exp(-5*Math.min(dt,.1)));
  }
  const ik=useMemo(()=>({shoulder:new Vector3(),elbow:new Vector3(),hand:new Vector3(),target:new Vector3(),direction:new Vector3(),pole:new Vector3(),desiredElbow:new Vector3(),from:new Vector3(),to:new Vector3(),world:new Quaternion(),parent:new Quaternion(),delta:new Quaternion()}),[]);
  function traceBoard(target:Vector3,dt:number) {
    if(!writingBoard || reduced)return;
    const upper=rig.bones.get('LeftArm'),lower=rig.bones.get('LeftForeArm'),hand=rig.bones.get('LeftHand');
    if(!upper||!lower||!hand)return;
    stage.current?.updateMatrixWorld(true);
    upper.node.getWorldPosition(ik.shoulder);lower.node.getWorldPosition(ik.elbow);hand.node.getWorldPosition(ik.hand);
    const a=ik.shoulder.distanceTo(ik.elbow),b=ik.elbow.distanceTo(ik.hand);
    // Keep the hand on the board side and IN FRONT of the torso. Unreachable
    // cursor positions become a pointing direction, never a twisted full reach.
    ik.target.set(MathUtils.clamp(target.x,ik.shoulder.x+.12,ik.shoulder.x+.5),MathUtils.clamp(target.y,ik.shoulder.y-.25,ik.shoulder.y+.16),ik.shoulder.z+.25);
    ik.direction.copy(ik.target).sub(ik.shoulder);
    const distance=MathUtils.clamp(ik.direction.length(),Math.abs(a-b)+.02,(a+b)*.94);
    ik.direction.normalize();ik.target.copy(ik.shoulder).addScaledVector(ik.direction,distance);
    const along=(a*a-b*b+distance*distance)/(2*distance);
    const bend=Math.sqrt(Math.max(0,a*a-along*along));
    ik.pole.set(0,-.3,1).addScaledVector(ik.direction,-(-.3*ik.direction.y+ik.direction.z)).normalize();
    ik.desiredElbow.copy(ik.shoulder).addScaledVector(ik.direction,along).addScaledVector(ik.pole,bend);
    const aim=(joint:typeof upper,child:Object3D,destination:Vector3,limit:number)=>{
      stage.current?.updateMatrixWorld(true);joint.node.getWorldPosition(ik.elbow);child.getWorldPosition(ik.hand);
      ik.from.copy(ik.hand).sub(ik.elbow).normalize();ik.to.copy(destination).sub(ik.elbow).normalize();
      ik.delta.setFromUnitVectors(ik.from,ik.to);joint.node.getWorldQuaternion(ik.world);joint.node.parent!.getWorldQuaternion(ik.parent).invert();
      ik.world.premultiply(ik.delta).premultiply(ik.parent);
      const angle=joint.rest.angleTo(ik.world);if(angle>limit){ik.parent.copy(ik.world);ik.world.copy(joint.rest).slerp(ik.parent,limit/angle);}
      joint.node.quaternion.slerp(ik.world,1-Math.exp(-7*Math.min(dt,.1)));
    };
    aim(upper,lower.node,ik.desiredElbow,1.65);aim(lower,hand.node,ik.target,2.3);
  }
  const stage=useRef<Group>(null);
  const screenTarget=useMemo(()=>new Vector3(),[]);
  const rayDirection=useMemo(()=>new Vector3(),[]);
  useFrame(({clock,camera,viewport}, dt) => {
    const t = clock.elapsedTime;
    const speaking = state === 'explaining';
    const happy = state === 'correct' || state === 'encouraging';
    const attentive = state === 'listening' || state === 'confused' || state === 'incorrect';
    if(event.current.stepNumber !== stepNumber) event.current={state,stepNumber,age:0};
    if(event.current.state !== state) {const resume=event.current.state==='paused'&&state==='explaining';event.current={state,stepNumber,age:state==='paused'||resume?event.current.age:0};}
    if(state!=='paused')event.current.age += dt;
    const age=event.current.age;
    const gesture=reduced?'rest':state==='explaining' && teachingGesture ? teachingGesture : gestureAt(state,speaking?speech.progress()*12:age,stepNumber);
    if(gesture!==lastGesture.current){lastGesture.current=gesture;onGesture(gesture);}
    const mouth = speaking ? speech.sample() : {};
    // Warm resting smile, dimples and lifted inner brows; frown and sneer forced off.
    // Gaze: whiteboard while teaching a step, student (camera) while talking or listening.
    const smile = (happy ? .95 : attentive ? .62 : state==='thinking' ? .55 : .78) * (speaking ? .68 : 1);
    const gazeBoard = speaking && !!writingBoard?.active;
    const gazeSide = gazeBoard ? .55 : 0, gazeDown = gazeBoard ? .32 : 0;
    const blinkPhase=t%5.3;
    const blink = reduced ? 0 : Math.max(0,1-Math.abs(blinkPhase-4.8)/.16);
    const values: Record<string,number> = {jawOpen:0, eyeBlinkLeft:blink,eyeBlinkRight:blink,
      mouthSmileLeft:smile,mouthSmileRight:smile,mouthDimpleLeft:smile*.35,mouthDimpleRight:smile*.35,
      mouthFrownLeft:0,mouthFrownRight:0,noseSneerLeft:0,noseSneerRight:0,
      cheekSquintLeft:happy?.3:.18,cheekSquintRight:happy?.3:.18,
      eyeSquintLeft:happy?.14:.06,eyeSquintRight:happy?.14:.06,
      eyeLookOutLeft:gazeSide,eyeLookInRight:gazeSide,eyeLookInLeft:0,eyeLookOutRight:0,
      eyeLookDownLeft:gazeDown,eyeLookDownRight:gazeDown,eyeLookUpLeft:0,eyeLookUpRight:0,
      browDownLeft:0,browDownRight:0,browInnerUp:attentive?.3:.18,
      browOuterUpLeft:state==='thinking'?.24:.12,browOuterUpRight:state==='thinking'?.2:.12};
    for(const v of visemes) values[`viseme_${v}`]=mouth[v] || 0;
    for (const mesh of rig.meshes) for (const [name, target] of Object.entries(values)) {
      const index = mesh.morphTargetDictionary?.[name];
      if (index !== undefined && mesh.morphTargetInfluences) mesh.morphTargetInfluences[index] = MathUtils.damp(mesh.morphTargetInfluences[index], target, 22, Math.min(dt, .1));
    }
    if (state === 'paused') return;
    const motion = reduced ? 0 : 1;
    bone('Head', motion*(.018*Math.sin(t*.9)+(happy && age<2.8?.045*Math.sin(age*3):0)+(speaking?.02*Math.sin(t*2.2):0)),motion*(gazeBoard?.22:.02*Math.sin(t*.5)),motion*(state==='thinking'?.045:(attentive||happy)?-.04:0),dt);
    bone('Spine2',0,writingBoard?.active?.08:0,motion*.006*Math.sin(t*1.4),dt);
    for(const side of ['Left','Right']) {
      const sign=side==='Left'?-1:1;
      const active=writingBoard ? !!writingBoard.active && side==='Left' : gesture==='open'||gesture==='celebrate'||(side==='Right'&&gesture!=='rest');
      const pointing=active&&gesture==='point';
      const counting=active&&gesture==='count';
      const raised=active?(gesture==='celebrate'?1.25:counting?1.4:pointing?.95:1.05):0;
      if(!(writingBoard&&active)){bone(`${side}Arm`,active?sign*(pointing?.32:.12):0,0,active?.14:0,dt);
      bone(`${side}ForeArm`,0,0,raised,dt);}
      if(active && !writingBoard) {rig.scene.updateMatrixWorld(true);orientHand(side,gesture,dt);} else bone(`${side}Hand`,0,0,0,dt);
      const count=Math.min(5,Math.max(1,stepNumber||1));
      for(const [i,finger] of ['Index','Middle','Ring','Pinky','Thumb'].entries()) {
        const curl=pointing ? finger!=='Index' && finger!=='Thumb' : counting ? finger!=='Thumb' && i>=count : false;
        for(const joint of [1,2,3]) bone(`${side}Hand${finger}${joint}`,curl?-sign*(joint===1?.3:.4):0,0,0,dt);
      }
    }
    if (writingBoard) {
      const screen=writingBoard.screen;
      if(screen){screenTarget.set(screen.x*2-1,1-screen.y*2,.5).unproject(camera);rayDirection.copy(screenTarget).sub(camera.position).normalize();screenTarget.copy(camera.position).addScaledVector(rayDirection,-camera.position.z/rayDirection.z);screenTarget.x+=HAND_SIDE_OFFSET;screenTarget.y+=HAND_LIFT_OFFSET;}
      else screenTarget.set(0,1.3,0);
      if(stage.current){const scale=Math.min(1,viewport.width/2);stage.current.scale.setScalar(scale);const margin=.3*scale;const target=-viewport.width*(scale<1?.34:.29);stage.current.position.x=MathUtils.clamp(MathUtils.damp(stage.current.position.x,target,4,Math.min(dt,.1)),-viewport.width/2+margin,viewport.width/2-margin);}
      if(writingBoard.active)traceBoard(screenTarget,dt);
    }
    if (root.current) {root.current.position.y = motion * .003 * Math.sin(t * 1.6); root.current.rotation.y = motion * .025 * Math.sin(t * .45);}
  });
  return <group ref={stage} position={writingBoard ? [-1,0,0] : [0,0,0]}><group ref={root}><primitive object={rig.scene} scale={rig.scale} position={[0, rig.y, 0]} dispose={null}/></group></group>;
}

export default function TeacherAvatar({state,speech,syncMode,stepNumber,teachingGesture,writingBoard}: PerformanceProps) {
  const [gesture,setGesture] = useState<Gesture>('rest');
  const [loaded, setLoaded] = useState(false);
  const [reduced, setReduced] = useState(false);
  const ready = useMemo(() => () => setLoaded(true), []);
  useEffect(() => {const query = matchMedia('(prefers-reduced-motion: reduce)'); const update = () => setReduced(query.matches); update(); query.addEventListener('change', update); return () => query.removeEventListener('change', update);}, []);
  return <div className={`teacher-3d ${writingBoard ? "teacher-writing-stage" : ""}`} role="img" aria-label={`Mia, 3D teacher, ${state}, ${gesture} gesture`}>
    <SceneBoundary><Canvas gl={{preserveDrawingBuffer:true}} dpr={[1, 1.5]} camera={{position: writingBoard ? [0,1.08,2.7] : [0, 1.48, 1.3], fov: writingBoard ? 40 : 32}} onCreated={({camera}) => camera.lookAt(0, writingBoard ? 1.08 : 1.35, 0)} fallback={<p className="avatar-fallback">3D needs WebGL. Voice and captions are still available.</p>}>
      <ambientLight intensity={1.3}/><hemisphereLight args={['#ffffff', '#7971a7', 1.2]}/>
      <directionalLight position={[2, 3, 4]} intensity={2.2}/><directionalLight position={[-2, 2, 1]} intensity={1}/>
      <Suspense fallback={null}><Human writingBoard={writingBoard} teachingGesture={teachingGesture} onGesture={setGesture} state={state} speech={speech} syncMode={syncMode} stepNumber={stepNumber} reduced={reduced} ready={ready}/></Suspense>
    </Canvas>
    {!loaded && <span className="avatar-loading" role="status">Loading Mia’s 3D studio…</span>}
    </SceneBoundary>
    <span className="avatar-state" aria-live="polite">{state === 'idle' ? 'Here for you' : state === 'explaining' ? 'Speaking' : state}</span>
  </div>;
}
