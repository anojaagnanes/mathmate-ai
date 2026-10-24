'use client';
import { Component, Suspense, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { Box3, Group, Matrix4, MathUtils, Mesh, MeshStandardMaterial, SkinnedMesh, Object3D, Quaternion, Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone } from 'three/addons/utils/SkeletonUtils.js';
import { gestureAt, type Gesture } from '@/lib/teacher-performance';
import { visemes, type LipSyncClock, type SyncMode } from '@/lib/lip-sync';
import type { TeacherState } from '@/lib/teacher-state';

class SceneBoundary extends Component<{children: ReactNode}, {failed: boolean}> {
  state = {failed: false};
  static getDerivedStateFromError() {return {failed: true};}
  render() {return this.state.failed ? <p className="avatar-fallback" role="alert">Mia’s 3D model could not load. You can still use the lesson, voice and captions. Reload to retry.</p> : this.props.children;}
}

type PerformanceProps = {state: TeacherState; speech: LipSyncClock; syncMode: SyncMode; stepNumber?: number};
function Human({state, speech, stepNumber, reduced, ready, onGesture}: PerformanceProps & {reduced: boolean; ready: () => void; onGesture: (gesture: Gesture) => void}) {
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
  useFrame(({clock}, dt) => {
    const t = clock.elapsedTime;
    const speaking = state === 'explaining';
    const happy = state === 'correct' || state === 'encouraging';
    const attentive = state === 'listening' || state === 'confused' || state === 'incorrect';
    if(event.current.stepNumber !== stepNumber) event.current={state,stepNumber,age:0};
    if(event.current.state !== state) {const resume=event.current.state==='paused'&&state==='explaining';event.current={state,stepNumber,age:state==='paused'||resume?event.current.age:0};}
    if(state!=='paused')event.current.age += dt;
    const age=event.current.age;
    const gesture=reduced?'rest':gestureAt(state,speaking?speech.progress()*12:age,stepNumber);
    if(gesture!==lastGesture.current){lastGesture.current=gesture;onGesture(gesture);}
    const mouth = speaking ? speech.sample() : {};
    // Smile + cheek lift, softened inner brows; reduce smile during articulation.
    const smile = (happy ? .90 : attentive ? .48 : state==='thinking' ? .42 : .65) * (speaking ? .55 : 1);
    const blinkPhase=t%5.3;
    const blink = reduced ? 0 : Math.max(0,1-Math.abs(blinkPhase-4.8)/.16);
    const values: Record<string,number> = {jawOpen:0, eyeBlinkLeft:blink,eyeBlinkRight:blink,
      mouthSmileLeft:smile,mouthSmileRight:smile,cheekSquintLeft:happy?.24:.12,cheekSquintRight:happy?.24:.12,
      eyeSquintLeft:happy?.12:.045,eyeSquintRight:happy?.12:.045,
      browDownLeft:0,browDownRight:0,browInnerUp:attentive?.22:.13,
      browOuterUpLeft:state==='thinking'?.22:.08,browOuterUpRight:state==='thinking'?.17:.08};
    for(const v of visemes) values[`viseme_${v}`]=mouth[v] || 0;
    for (const mesh of rig.meshes) for (const [name, target] of Object.entries(values)) {
      const index = mesh.morphTargetDictionary?.[name];
      if (index !== undefined && mesh.morphTargetInfluences) mesh.morphTargetInfluences[index] = MathUtils.damp(mesh.morphTargetInfluences[index], target, 22, Math.min(dt, .1));
    }
    const motion = reduced ? 0 : 1;
    bone('Head', motion*(.018*Math.sin(t*.9)+(happy && age<2.8?.045*Math.sin(age*3):0)),motion*.025*Math.sin(t*.5),motion*(state==='thinking'?.045:attentive?-.035:0),dt);
    bone('Spine2',0,0,motion*.006*Math.sin(t*1.4),dt);
    for(const side of ['Left','Right']) {
      const sign=side==='Left'?-1:1;
      const active=gesture==='open'||gesture==='celebrate'||(side==='Right'&&gesture!=='rest');
      const pointing=active&&gesture==='point';
      const counting=active&&gesture==='count';
      const raised=active?(gesture==='celebrate'?1.25:counting?1.4:pointing?.95:1.05):0;
      bone(`${side}Arm`,active?sign*(pointing?.32:.12):0,0,active?.14:0,dt);
      bone(`${side}ForeArm`,0,0,raised,dt);
      if(active) {rig.scene.updateMatrixWorld(true);orientHand(side,gesture,dt);} else bone(`${side}Hand`,0,0,0,dt);
      const count=Math.min(5,Math.max(1,stepNumber||1));
      for(const [i,finger] of ['Index','Middle','Ring','Pinky','Thumb'].entries()) {
        const curl=pointing ? finger!=='Index' && finger!=='Thumb' : counting ? finger!=='Thumb' && i>=count : false;
        for(const joint of [1,2,3]) bone(`${side}Hand${finger}${joint}`,curl?-sign*(joint===1?.3:.4):0,0,0,dt);
      }
    }
    if (root.current) {root.current.position.y = motion * .003 * Math.sin(t * 1.6); root.current.rotation.y = motion * .025 * Math.sin(t * .45);}
  });
  return <group ref={root}><primitive object={rig.scene} scale={rig.scale} position={[0, rig.y, 0]} dispose={null}/></group>;
}

export default function TeacherAvatar({state,speech,syncMode,stepNumber}: PerformanceProps) {
  const [gesture,setGesture] = useState<Gesture>('rest');
  const [loaded, setLoaded] = useState(false);
  const [reduced, setReduced] = useState(false);
  const ready = useMemo(() => () => setLoaded(true), []);
  useEffect(() => {const query = matchMedia('(prefers-reduced-motion: reduce)'); const update = () => setReduced(query.matches); update(); query.addEventListener('change', update); return () => query.removeEventListener('change', update);}, []);
  return <div className="teacher-3d" role="img" aria-label={`Mia, 3D human teacher, ${state}, ${gesture} gesture`}>
    <SceneBoundary><Canvas dpr={[1, 1.5]} camera={{position: [0, 1.48, 1.3], fov: 32}} onCreated={({camera}) => camera.lookAt(0, 1.35, 0)} fallback={<p className="avatar-fallback">3D needs WebGL. Voice and captions are still available.</p>}>
      <ambientLight intensity={1.3}/><hemisphereLight args={['#ffffff', '#7971a7', 1.2]}/>
      <directionalLight position={[2, 3, 4]} intensity={2.2}/><directionalLight position={[-2, 2, 1]} intensity={1}/>
      <Suspense fallback={null}><Human onGesture={setGesture} state={state} speech={speech} syncMode={syncMode} stepNumber={stepNumber} reduced={reduced} ready={ready}/></Suspense>
    </Canvas>
    {!loaded && <span className="avatar-loading" role="status">Loading Mia’s 3D studio…</span>}
    </SceneBoundary>
    <span className="avatar-state" aria-live="polite">{state === 'idle' ? 'Here for you' : state === 'explaining' ? syncMode==='provider'?'Speaking · audio-timed visemes':syncMode==='word'?'Speaking · word-aligned estimate':'Speaking · estimated visemes' : state}</span>
  </div>;
}
