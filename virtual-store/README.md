# Virtual Store Example (Next.js + THREE.js)

This folder contains a simple [Next.js](https://nextjs.org/) project that displays a 3D room using [THREE.js](https://threejs.org/). A hand model can walk to a target object and play a pick-up animation on click.

## Setup

1. Navigate to this directory:
   ```bash
   cd virtual-store
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Copy your FBX models into `public/models/`:
   - `Hand_Rif.fbx`
   - `Idle.fbx`
   - `Walk.fbx`
   - `Pick_Up.fbx`
   The sample scene expects these exact file names.
4. Start the development server:
   ```bash
   npm run dev
   ```
5. Open `http://localhost:3000` in your browser.

**Note:** The 3D library used here is **THREE.js**, not "TierJS".
