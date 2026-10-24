import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone} from 'three/addons/utils/SkeletonUtils.js';
import {Box3,SkinnedMesh} from 'three';
// Validate the shipped rig without a browser or texture decoder.
const bytes=await readFile(new URL('../public/models/mia/teacher.glb',import.meta.url));
const loader=new GLTFLoader();loader.register(()=>({name:'NO_TEXTURES',loadTexture:()=>Promise.resolve(null)}));
const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
const scene=clone(gltf.scene);
scene.updateMatrixWorld(true);
let meshes=0;
scene.traverse(n=>{if(n instanceof SkinnedMesh){n.skeleton.update();n.computeBoundingBox();meshes++;}});
const bounds=new Box3().setFromObject(scene,true);
assert.ok(meshes>0,'Must contain real skinned geometry');
assert.ok(bounds.max.y-bounds.min.y>1.5 && bounds.max.y-bounds.min.y<1.9,'Initialized cloned rig must retain human scale');
assert.ok(scene.getObjectByName('Head'),'Head bone required');
for(const side of ['Left','Right']) for(const finger of ['Index','Middle','Ring','Pinky','Thumb']) for(const joint of [1,2,3]) assert.ok(scene.getObjectByName(`${side}Hand${finger}${joint}`),'Articulated finger bone required');
for(const name of ['viseme_PP','viseme_aa','viseme_FF','jawOpen','eyeBlinkLeft','eyeBlinkRight','mouthSmileLeft','mouthSmileRight']) {
 let maxDelta=0;
 scene.traverse(n=>{if(n instanceof SkinnedMesh){const index=n.morphTargetDictionary?.[name];const a=n.geometry.morphAttributes.position?.[index];if(a) for(let i=0;i<a.array.length;i++)maxDelta=Math.max(maxDelta,Math.abs(a.array[i]));}});
 assert.ok(maxDelta>.0001,`${name} must actually deform vertices`);
}
console.log('PASS: skinned human model, initialized clone scale, head rig, jaw, blink and smile geometry.');
