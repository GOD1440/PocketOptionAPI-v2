import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader';

export default function Home() {
  const mountRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    const width = mount.clientWidth;
    const height = mount.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xeeeeee);

    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(0, 1.6, 5);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    mount.appendChild(renderer.domElement);

    const ambient = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambient);
    const directional = new THREE.DirectionalLight(0xffffff, 0.5);
    directional.position.set(5, 10, 2);
    scene.add(directional);

    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(10, 10),
      new THREE.MeshStandardMaterial({ color: 0x808080 })
    );
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    const wallMaterial = new THREE.MeshStandardMaterial({ color: 0xdddddd });
    const backWall = new THREE.Mesh(new THREE.PlaneGeometry(10, 4), wallMaterial);
    backWall.position.set(0, 2, -5);
    scene.add(backWall);
    const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(10, 4), wallMaterial);
    leftWall.position.set(-5, 2, 0);
    leftWall.rotation.y = Math.PI / 2;
    scene.add(leftWall);
    const rightWall = leftWall.clone();
    rightWall.position.set(5, 2, 0);
    rightWall.rotation.y = -Math.PI / 2;
    scene.add(rightWall);

    const box = new THREE.Mesh(
      new THREE.BoxGeometry(0.3, 0.3, 0.3),
      new THREE.MeshStandardMaterial({ color: 0xff0000 })
    );
    box.position.set(0, 0.15, -2);
    box.name = 'target';
    scene.add(box);

    const loader = new FBXLoader();
    let mixer;
    let handModel;
    const actions = {};
    let targetZ = null;

    const loadAnim = (file, name) => {
      loader.load(file, anim => {
        const action = mixer.clipAction(anim.animations[0]);
        action.loop = THREE.LoopRepeat;
        actions[name] = action;
        if (name === 'Idle') action.play();
      });
    };

    loader.load('/models/Hand_Rif.fbx', model => {
      model.scale.set(0.01, 0.01, 0.01);
      scene.add(model);
      handModel = model;
      mixer = new THREE.AnimationMixer(model);
      loadAnim('/models/Idle.fbx', 'Idle');
      loadAnim('/models/Walk.fbx', 'Walk');
      loadAnim('/models/Pick_Up.fbx', 'Pick_Up');
    });

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const onClick = event => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects([box]);
      if (intersects.length > 0 && handModel) {
        targetZ = box.position.z;
        actions['Idle']?.stop();
        actions['Pick_Up']?.stop();
        actions['Walk']?.reset().play();
      }
    };
    window.addEventListener('click', onClick);

    const clock = new THREE.Clock();
    function animate() {
      requestAnimationFrame(animate);
      const delta = clock.getDelta();
      mixer?.update(delta);

      if (handModel && targetZ !== null) {
        handModel.position.z -= delta;
        if (handModel.position.z <= targetZ) {
          handModel.position.z = targetZ;
          targetZ = null;
          actions['Walk']?.stop();
          actions['Pick_Up']?.reset().play();
        }
      }

      renderer.render(scene, camera);
    }
    animate();

    const handleResize = () => {
      const { clientWidth, clientHeight } = mount;
      camera.aspect = clientWidth / clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(clientWidth, clientHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('click', onClick);
      mount.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={mountRef} style={{ width: '100%', height: '100vh' }} />;
}
