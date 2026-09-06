# Project Front Log & Component Code Registry (`front.md`)

> **Project Name:** STHack Web App  
> **Tech Stack:** React 19, Tailwind CSS v4, Vite, WebGPU (vgpu), OGL WebGL, Lucide Icons  
> **Last Updated:** 2026-09-04  

---

## 🎨 Global & Shared Component Code Registry

### 1. Circular Favicon
- **Prompt Reference:** Prompt #3, #22, #39
- **Code:** `public/favicon.svg` & `index.html`
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="alternate icon" type="image/png" href="/favicon.png" />
```
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <defs>
    <clipPath id="circleClip">
      <circle cx="64" cy="64" r="64" />
    </clipPath>
  </defs>
  <g clip-path="url(#circleClip)">
    <rect width="128" height="128" fill="#000000" />
    <image href="/logo.png" width="128" height="128" preserveAspectRatio="xMidYMid slice" />
  </g>
</svg>
```

---

### 2. Explore Page Button (Shared across all pages in Hero section)
- **Prompt Reference:** Prompt #10, #11
- **Code:** `HeroSection.jsx`
```jsx
<button
  type="button"
  className={`relative z-10 inline-flex items-center justify-center gap-3 px-7 py-3.5 text-lg font-semibold border-2 rounded-full shadow-xl overflow-hidden group cursor-pointer transition-all duration-500 hover:text-white hover:border-emerald-500 ${
    darkMode ? 'bg-white text-slate-900 border-white' : 'bg-gray-50 text-slate-900 border-slate-200'
  }`}
>
  {/* Emerald Background Fill Layer */}
  <span className="absolute inset-0 w-full h-full bg-emerald-500 rounded-full -translate-x-full group-hover:translate-x-0 transition-transform duration-500 ease-out z-0 pointer-events-none" />

  <span className="relative z-10 font-bold">Explore {pageName}</span>

  {/* Rotating Arrow SVG */}
  <svg
    className={`relative z-10 w-8 h-8 group-hover:rotate-90 group-hover:bg-white ease-linear duration-300 rounded-full border group-hover:border-none p-1.5 rotate-45 shrink-0 shadow-xs ${
      darkMode ? 'bg-slate-900 text-white border-slate-700' : 'bg-gray-50 text-slate-800 border-slate-300'
    }`}
    viewBox="0 0 16 19"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M7 18C7 18.5523 7.44772 19 8 19C8.55228 19 9 18.5523 9 18H7ZM8.70711 0.292893C8.31658 -0.0976311 7.68342 -0.0976311 7.29289 0.292893L0.928932 6.65685C0.538408 7.04738 0.538408 7.68054 0.928932 8.07107C1.31946 8.46159 1.95262 8.46159 2.34315 8.07107L8 2.41421L13.6569 8.07107C14.0474 8.46159 14.6805 8.46159 15.0711 8.07107C15.4616 7.68054 15.4616 7.04738 15.0711 6.65685L8.70711 0.292893ZM9 18L9 1H7L7 18H9Z"
      className={darkMode ? 'fill-white group-hover:fill-emerald-600 transition-colors' : 'fill-slate-800 group-hover:fill-emerald-600 transition-colors'}
    ></path>
  </svg>
</button>
```

---

### 3. View Docs Specular Button (Shared across all pages in Hero section)
- **Prompt Reference:** Prompt #4, #6
- **Code:** `SpecularButton.jsx` & `HeroSection.jsx`
```jsx
<SpecularButton
  size="lg"
  radius={9999}
  tint={darkMode ? "#0f172a" : "#ffffff"}
  tintOpacity={darkMode ? 0.75 : 0.9}
  textColor={darkMode ? "#ffffff" : "#0f172a"}
  lineColor={darkMode ? "#c084fc" : "#4f46e5"}
  baseColor={darkMode ? "#334155" : "#cbd5e1"}
  intensity={1.2}
  shineSize={14}
  shineFade={35}
  thickness={1.5}
  speed={0.35}
  followMouse={true}
  proximity={250}
>
  <Terminal className={`w-4.5 h-4.5 ${darkMode ? 'text-indigo-400' : 'text-indigo-600'}`} />
  <span>View Docs</span>
</SpecularButton>
```

---

## 🚀 Page 1 Background & Components

### Page 1 Background (`<AeroShards />`)
- **Prompt Reference:** Prompt #5, #6
- **Code:** `AeroShards.jsx` & `HeroSection.jsx`
```jsx
<AeroShards
  backgroundColor={darkMode ? "#0b0f17" : "#ffffff"}
  shardColor={darkMode ? "#a855f7" : "#4f46e5"}
  accentColor={darkMode ? "#c084fc" : "#818cf8"}
  placement="full"
  flow="stream"
  material="pearl"
  detail="balanced"
  speed={0.9}
  scale={1.1}
  density={1.3}
  glow={darkMode ? 0.9 : 0.7}
  bloom={darkMode ? 0.6 : 0.4}
  holdToGather={false}
/>
```

---

## ⚡ Page 2 Background & Card Button Effects

### Page 2 Background (`<Threads />`)
- **Prompt Reference:** Prompt #25
- **Code:** `Threads.jsx` & `PageCanvas.jsx`
```jsx
<Threads 
  color={darkMode ? [0.75, 0.52, 0.99] : [0.31, 0.27, 0.95]}
  amplitude={1.2}
  distance={0}
  enableMouseInteraction={true}
/>
```

### Page 2 Card 1 Button Style & Hover Effect (Teal Pulse)
- **Prompt Reference:** Prompt #26
- **CSS Code:** `src/index.css`
```css
@keyframes pulseTeal {
  0% { 
    box-shadow: 0 0 0 0 rgba(100, 255, 218, 0.6); 
  }
  100% { 
    box-shadow: 0 0 0 16px rgba(100, 255, 218, 0); 
  }
}

.btn-pulse-teal {
  border: 2px solid #64ffda;
  border-radius: 50px;
  color: #64ffda;
  background: transparent;
  transition: all 0.3s ease;
}

.btn-pulse-teal:hover {
  animation: pulseTeal 1s ease-out;
  box-shadow: 0 0 20px rgba(100, 255, 218, 0.15);
}
```
- **JSX Code:** `PageCanvas.jsx`
```jsx
<button 
  type="button"
  className="btn-pulse-teal w-full py-3 text-sm font-bold tracking-wide flex items-center justify-center gap-2 group"
>
  <span>Launch Telemetry</span>
  <span className="transition-transform group-hover:translate-x-1">&rarr;</span>
</button>
```

### Page 2 Card 2 Button Style & Hover Effect (#00FF00 Matrix Scan Line)
- **Prompt Reference:** Prompt #27, #28, #29
- **CSS Code:** `src/index.css`
```css
@keyframes scan {
  0%   { top: -100%; }
  100% { top: 200%; }
}

.btn-scan-matrix {
  background: rgba(0, 255, 0, 0.05);
  border: 1.5px solid rgba(0, 255, 0, 0.4);
  color: #00FF00;
  font-family: 'Courier New', Courier, monospace;
  text-transform: uppercase;
  position: relative;
  z-index: 1;
  overflow: hidden;
  border-radius: 50px;
  transition: all 0.3s ease;
}

.btn-scan-matrix::after {
  content: '';
  position: absolute;
  top: -100%;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    transparent 30%,
    rgba(0, 255, 0, 0.25) 50%,
    transparent 70%
  );
  z-index: -1;
}

.btn-scan-matrix:hover::after {
  animation: scan 1.2s ease-in-out infinite;
}

.btn-scan-matrix:hover {
  text-shadow: 0 0 8px rgba(0, 255, 0, 0.7);
  border-color: #00FF00;
  box-shadow: 0 0 15px rgba(0, 255, 0, 0.25);
}
```
- **JSX Code:** `PageCanvas.jsx`
```jsx
<button 
  type="button"
  className="btn-scan-matrix w-full py-3 text-sm font-bold tracking-wider flex items-center justify-center gap-2 cursor-pointer group"
>
  <span>Analyze Threats</span>
  <span className="transition-transform group-hover:translate-x-1">&rarr;</span>
</button>
```

### Page 2 Card 3 Button Style & Hover Effect (Conic Spotlight Gold Beam)
- **Prompt Reference:** Prompt #30
- **CSS Code:** `src/index.css`
```css
@property --angle {
  syntax: '<angle>';
  initial-value: 0deg;
  inherits: false;
}

@keyframes spotlight {
  to { --angle: 360deg; }
}

.btn-conic-spotlight {
  --angle: 0deg;
  background: conic-gradient(
    from var(--angle),
    transparent 0%,
    rgba(255, 200, 50, 0.2) 10%,
    transparent 20%
  ), #1a1a2a;
  border: 1px solid rgba(255, 200, 50, 0.3);
  border-radius: 50px;
  color: #ffc832;
  transition: all 0.3s ease;
}

.btn-conic-spotlight:hover {
  animation: spotlight 2s linear infinite;
  border-color: rgba(255, 200, 50, 0.6);
  box-shadow: 0 0 20px rgba(255, 200, 50, 0.2);
}
```
- **JSX Code:** `PageCanvas.jsx`
```jsx
<button 
  type="button"
  className="btn-conic-spotlight w-full py-3 text-sm font-bold tracking-wide flex items-center justify-center gap-2 cursor-pointer group"
>
  <span>Explore Mesh</span>
  <span className="transition-transform group-hover:translate-x-1">&rarr;</span>
</button>
```

---

## 🌊 Page 3 Background & Card Button Effects

### Page 3 Background (`<Ferrofluid />`)
- **Prompt Reference:** Prompt #31, #32, #33
- **Code:** `Ferrofluid.jsx` & `PageCanvas.jsx`
```jsx
<Ferrofluid 
  colors={["#ffffff", "#ffffff", "#ffffff"]}
  speed={0.5}
  scale={1}
  turbulence={1}
  fluidity={0.1}
  rimWidth={0.2}
  sharpness={3}
  shimmer={1}
  glow={2}
  flowDirection="down"
  opacity={1}
  mouseInteraction={true}
  mouseStrength={1}
  mouseRadius={0.3}
/>
```

### Page 3 Card 1 Button Style & Hover Effect (Black Stepped White Stacked Shadow)
- **Prompt Reference:** Prompt #34, #35
- **CSS Code:** `src/index.css`
```css
.btn-stacked-shadow {
  background: #141414;
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.25);
  font-weight: 700;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.btn-stacked-shadow:hover {
  background: #000000;
  color: #ffffff;
  box-shadow:
    0 2px 0 rgba(255, 255, 255, 0.7),
    0 5px 0 rgba(255, 255, 255, 0.5),
    0 9px 0 rgba(255, 255, 255, 0.3),
    0 14px 0 rgba(255, 255, 255, 0.15),
    0 20px 0 rgba(255, 255, 255, 0.06);
  transform: translateY(-4px);
}
```
- **JSX Code:** `PageCanvas.jsx`
```jsx
<button 
  type="button"
  className="btn-stacked-shadow w-full py-3.5 text-sm font-bold tracking-wide flex items-center justify-center gap-2 cursor-pointer group"
>
  <span>Initialize Fluid</span>
  <span className="transition-transform group-hover:translate-x-1">&rarr;</span>
</button>
```

### Page 3 Card 2 Button Style & Hover Effect (Monospace Letter Tracking Squeeze)
- **Prompt Reference:** Prompt #34
- **CSS Code:** `src/index.css`
```css
.btn-letter-squeeze {
  background: #1a1a1a;
  color: #f7f3ee;
  border: 2px solid #1a1a1a;
  font-family: 'Courier New', Courier, monospace;
  font-weight: 700;
  letter-spacing: 6px;
  text-transform: uppercase;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 4px;
}

.btn-letter-squeeze:hover {
  letter-spacing: 1px;
  background: #f7f3ee;
  color: #1a1a1a;
  transform: scale(0.97);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.15);
}
```
- **JSX Code:** `PageCanvas.jsx`
```jsx
<button 
  type="button"
  className="btn-letter-squeeze w-full py-3 text-xs font-bold flex items-center justify-center gap-2 cursor-pointer group"
>
  <span>Engage Field</span>
  <span className="transition-transform group-hover:translate-x-1">&rarr;</span>
</button>
```

### Page 3 Card 3 Button Style & Hover Effect (Sky Blue #93c5fd Soft Glow Aura)
- **Prompt Reference:** Prompt #36, #37, #38
- **CSS Code:** `src/index.css`
```css
.btn-sky-glow {
  background: rgba(147, 197, 253, 0.08);
  border: 2px solid rgba(147, 197, 253, 0.3);
  border-radius: 8px;
  color: #93c5fd;
  font-weight: 700;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-sky-glow:hover {
  background: rgba(147, 197, 253, 0.15);
  border-color: #fff;
  color: #fff;
  box-shadow:
    0 0 15px rgba(147, 197, 253, 0.4),
    0 0 40px rgba(147, 197, 253, 0.2),
    inset 0 0 15px rgba(200, 220, 255, 0.1);
  text-shadow: 0 0 8px rgba(200, 230, 255, 0.6);
  letter-spacing: 2px;
}
```
- **JSX Code:** `PageCanvas.jsx`
```jsx
<button 
  type="button"
  className="btn-sky-glow w-full py-3 text-sm font-bold tracking-wide flex items-center justify-center gap-2 cursor-pointer group"
>
  <span>Explore Shimmer</span>
  <span className="transition-transform group-hover:translate-x-1">&rarr;</span>
</button>
```

---

## 🧵 Page 4 Background & Components

### Page 4 Background (`<WebThreads />`)
- **Prompt Reference:** Prompt #40
- **Code:** `WebThreads.jsx` & `PageCanvas.jsx`
```jsx
<WebThreads
  color1="#5227FF"
  color2="#FF9FFC"
  color3="#FFFFFF"
  speed={0.2}
  threadCount={6}
  frequency={5.0}
  spread={0.18}
  taper={1.0}
  position={0.5}
  fanMode="center"
  glow={0.02}
  falloff={0.6}
  thickness={1.1}
  brightness={0.6}
  opacity={1.0}
  mirror={true}
  shimmer={false}
  grain={true}
  grainIntensity={0.05}
  mouseInteraction={true}
  mouseStrength={0.3}
/>
```

---

## 📜 Full Prompt Log & History

### Prompt #1 (Initial Setup)
- **User Request:** Create a website with React and Tailwind CSS, leave the page blank, make tabs named `Page1`, `Page2`, so on, and prepare a `front.md` file and keep updating it.
- **Action Taken:** Initialized Vite + React app with Tailwind CSS v4, established tab routing, created `PageCanvas`, and initialized `front.md`.

### Prompt #2 (Cognism Header Redesign)
- **User Request:** Update header layout and styling to match the attached photo (Cognism header reference).
- **Action Taken:** Built `Navbar.jsx` with Cognism header structure, white corporate styling, and navigation links.

### Prompt #3 (Custom Eye Emblem Logo, Favicon, Skeleton Loader & Header Cleanup)
- **User Request:** Remove "+ Add Tab", keep only Login button, dynamically align name `sthack`, add a skeleton loading page, and use attached image as logo and favicon.
- **Action Taken:** Integrated `/logo.png`, updated `index.html` title & favicon, created `SkeletonLoader.jsx` with `WifiLoader`, and streamlined `Navbar.jsx`.

### Prompt #4 (Hero Section with Side Background Cards & Clean Center)
- **User Request:** Add a hero section with sides having this background on each side, keep the center normal.
- **Action Taken:** Created initial `HeroSection.jsx` layout with background containers and centered typography.

### Prompt #5 (AeroShards WebGPU Background Integration on Hero Sides)
- **User Request:** Integrate `<AeroShards />` React Bits component (dependency: `vgpu`). Add this background on each side, keep the center plain.
- **Action Taken:** Installed `vgpu`, created `AeroShards.jsx` WebGPU wind sculpture component, and integrated into `HeroSection.jsx`.

### Prompt #6 (Unified Single Hero Section with Side AeroShards Background)
- **User Request:** Remove those cards and make one hero section with the background provided.
- **Action Taken:** Simplified `HeroSection.jsx` into one spacious hero banner with full-bleed AeroShards background.

### Prompt #7 (Header Layout Spacing Adjustments)
- **User Request:** Add more spacing between pages and move sthack a bit left and login a bit right.
- **Action Taken:** Increased inner container padding in `Navbar.jsx` and added `gap-12 lg:gap-16 xl:gap-20` between tab links.

### Prompt #8 (Animated Lock Hover Effect on Login Button)
- **User Request:** Keep the login button as it is but when hovered make a tiny animation of a lock showing up and locking itself; animation should play once per hover.
- **Action Taken:** Built lock micro-animation in `Navbar.jsx` login button with CSS keyframe transitions.

### Prompt #9 (Lock Icon Positioning & Animation Speed Adjustments)
- **User Request:** Slow down and move that to right side of login button.
- **Action Taken:** Repositioned lock SVG to right side of "Login" text and slowed duration to `500ms`.

### Prompt #10 (Uiverse.io Animated Explore Button Integration)
- **User Request:** Add Uiverse.io button effect with expanding background and rotating arrow SVG.
- **Action Taken:** Converted Uiverse button into React JSX CTA in `HeroSection.jsx`.

### Prompt #11 (Button Background Fill Fix)
- **User Request:** Color isn't filling make sure it fills it.
- **Action Taken:** Added absolute 100% width/height background fill span (`-translate-x-full group-hover:translate-x-0 bg-emerald-500`) ensuring complete background fill on hover.

### Prompt #12 (Uiverse.io Dark/Light Theme Toggle Switch Integration)
- **User Request:** Add toggle button for dark and light theme, and instead of aeroplane, add the logo image instead.
- **Action Taken:** Built `ThemeToggle.jsx` with Uiverse `.plane-switch` CSS and eye emblem logo image inside sliding knob.

### Prompt #15 (Uiverse.io Wifi Loader Integration)
- **User Request:** Add this loader effect (`#wifi-loader` from Uiverse.io by mobinkakei).
- **Action Taken:** Created `WifiLoader.jsx` with concentric animated SVG rings and integrated into `SkeletonLoader.jsx`.

### Prompt #20 (Glassmorphic Sky & Cloud Login Page Modal Integration)
- **User Request:** Add this for my login page (reference image attached).
- **Action Taken:** Created `LoginPageModal.jsx` featuring photo-realistic sky background, glassmorphic card, eye emblem avatar, and social sign-in buttons.

### Prompt #21 (Pixel-Perfect Login Modal Refinement)
- **User Request:** That doesn't look like the reference make it more refined.
- **Action Taken:** Refined border (`border-[3px] border-white`), centered avatar badge, orbital SVG rings, and charcoal `#1E1E1E` button styling.

### Prompt #22 (Rounded Brand Logo & Animated Sign Up Form Button Integration)
- **User Request:** Make my logo round its square and odd and add a signup button beside the login page and for that make an animation of a tiny form coming up and when clicked.
- **Action Taken:** Made logo containers perfectly circular (`rounded-full`), added header `Sign Up` button, and built compact slide-up form keyframes (`.animate-slide-up-form`).

### Prompt #23 (Header Sign Up Button Micro-Form Popover Animation)
- **User Request:** With the sign up button add a tiny animation of a form appearing.
- **Action Taken:** Added micro-animated form clipboard SVG icon inside the header `Sign Up` button.

### Prompt #24 (Streamlined Tiny Animated Sign Up Form Modal)
- **User Request:** Just a tiny form is enough not need for QUICK JOIN form.
- **Action Taken:** Streamlined Sign Up flow to trigger the glassmorphic modal with smooth slide-up form animation.

### Prompt #25 (React Bits <Threads /> OGL Integration on Page2)
- **User Request:** Add this to page2 dont cahnge color pallet (React Bits Threads component).
- **Action Taken:** Built `Threads.jsx` WebGL component using `ogl` and integrated onto Page2.

### Prompt #26 (Page2 Feature Cards Grid & Custom Teal Pulse Button Integration)
- **User Request:** Add three card in Page2 and for the first card button add this effect in tailwind css (.btn #64ffda pulse animation).
- **Action Taken:** Added `.btn-pulse-teal` CSS rule to `src/index.css` and built 3 feature cards grid on Page2.

### Prompt #27 (Green Matrix Scan Line Button Effect for Card 2)
- **User Request:** For second button add this effect in tailwind css (.btn #00ff41 matrix scan animation).
- **Action Taken:** Added `@keyframes scan` and `.btn-scan-matrix` CSS rule to `src/index.css`.

### Prompt #28 (Neutral Silver/Slate Palette for Card 2 Scan Button)
- **User Request:** For the second button keep the color neutral its hurting eye.
- **Action Taken:** Updated scan line button to neutral silver/slate tones.

### Prompt #29 (#00FF00 Electric Lime Matrix Scan Line Color Update)
- **User Request:** Make #ooFFoo color.
- **Action Taken:** Updated `.btn-scan-matrix` to pure `#00FF00` electric lime green color scheme.

### Prompt #30 (Conic Spotlight Gold Beam Button Effect for Card 3)
- **User Request:** Add this button style for third button tailwind css (@property --angle conic-gradient spotlight animation).
- **Action Taken:** Added `@property --angle`, `@keyframes spotlight`, and `.btn-conic-spotlight` gold beam rule to `src/index.css`.

### Prompt #31 (React Bits <Ferrofluid /> WebGL Background Integration on Page3)
- **User Request:** For the third page add this background (React Bits Ferrofluid component using OGL).
- **Action Taken:** Created `Ferrofluid.jsx` WebGL shader component and integrated as Page3 background.

### Prompt #32 (Ferrofluid WebGL Color Palette & Surface Sheen Enhancement)
- **User Request:** Why is the ferrofluid black?
- **Action Taken:** Explained shader color calculation and added vibrant multi-hue palette option.

### Prompt #33 (Restored Original Pitch-Black Ferrofluid Look)
- **User Request:** Noo make it black like previous.
- **Action Taken:** Reverted shader calculation to `vec3 outc = col * ltn`, restoring original pitch-black ferrofluid aesthetic.

### Prompt #34 (Page3 3 Feature Cards Grid & Custom Button Effects)
- **User Request:** Add three cards and add this button effect for first one (.btn-stacked-shadow) second button (.btn-letter-squeeze).
- **Action Taken:** Added 3 feature cards grid to Page3 with `.btn-stacked-shadow` and `.btn-letter-squeeze` custom CSS buttons.

### Prompt #35 (Black Styling for First Card Stacked Shadow Button)
- **User Request:** Change the color of first one to black.
- **Action Taken:** Updated `.btn-stacked-shadow` to black background (`#141414`) with white text and 3D white step shadow on hover.

### Prompt #36 (Page3 3rd Card Neutral Soft Glow Aura Button Effect)
- **User Request:** Page 3, 3rd button add this effect with neutral color.
- **Action Taken:** Added `.btn-neutral-glow` soft glow aura button effect.

### Prompt #37 (Black Styling for Page3 3rd Card Glow Aura Button)
- **User Request:** Make it black color.
- **Action Taken:** Updated `.btn-neutral-glow` base background to black (`#141414`).

### Prompt #38 (Exact Sky Blue #93c5fd Soft Glow Aura Button Effect for Page3 3rd Button)
- **User Request:** Add this effect to the third button in 3rd page (exact rgba(147, 197, 253, ...) snippet).
- **Action Taken:** Added `.btn-sky-glow` matching exact sky blue CSS snippet (`#93c5fd` text, `0 0 15px rgba(147, 197, 253, 0.4)` glow aura).

### Prompt #39 (Circular Favicon & Comprehensive Code Registry Format)
- **User Request:** Make the favicon round and for every button add the hover effect, background effect totally every code in the .md file make it this way... basically i need every element, component and effects code mentioned with code and the prompt too.
- **Action Taken:** Created circular `public/favicon.svg` with clipPath circle mask, updated `index.html` link, and restructured `front.md` into an exhaustive component & effect code registry.

### Prompt #40 (React Bits <WebThreads /> OGL Integration on Page4)
- **User Request:** Add this background to page4 (React Bits WebThreads component using OGL).
- **Action Taken:**
  - Created [`WebThreads.jsx`](file:///d:/sthack/src/components/WebThreads/WebThreads.jsx) and [`WebThreads.css`](file:///d:/sthack/src/components/WebThreads/WebThreads.css) WebGL 2.0 component powered by `ogl`.
  - Configured WebGL 2.0 fragment shader uniforms for multi-thread weaving (`threadCount={6}`), frequency, spread, fanMode pinch point, glow bloom, and cursor interaction.
  - Updated [`HeroSection.jsx`](file:///d:/sthack/src/components/HeroSection.jsx) to render `<WebThreads />` when `pageName === 'Page4'`.
  - Updated [`PageCanvas.jsx`](file:///d:/sthack/src/components/PageCanvas.jsx) to render `<WebThreads />` as the full-screen dynamic background container on **Page4** (`activeTab === 'page4'`).
  - Updated prompt log register in [`front.md`](file:///d:/sthack/front.md).

### Prompt #41 (Page4 WebThreads Uniform Palette Alignment)
- **User Request:** Page 4 keep the color whatever is in the below card not the neon blue.
- **Action Taken:**
  - Updated `<WebThreads />` props in [`HeroSection.jsx`](file:///d:/sthack/src/components/HeroSection.jsx) to match the lower card container colors strictly (`color1="#5227FF"`, `color2="#FF9FFC"`, `color3="#FFFFFF"`), removing neon cyan blue (`#06b6d4`).
  - Updated prompt log register in [`front.md`](file:///d:/sthack/front.md).

### Prompt #42 (Git Initialization & GitHub Repository Deployment)
- **User Request:** Push this to my github ill host this later in github pages https://github.com/Shiva-Prasad-ai/code-impulse.git
- **Action Taken:**
  - Initialized git repository (`git init`).
  - Configured git branch to `main` (`git branch -M main`).
  - Committed all project files & components (`git add .` & `git commit`).
  - Linked remote origin (`https://github.com/Shiva-Prasad-ai/code-impulse.git`).
  - Pushed codebase to GitHub repository `origin/main`.
  - Updated prompt log register in [`front.md`](file:///d:/sthack/front.md).

### Prompt #43 (Fixing GitHub Pages White Blank Page Issue)
- **User Request:** There is an issue i can only see white page in my live page from github.
- **Action Taken:**
  - **Identified Root Cause:** Vite defaults to absolute domain root asset paths (`/assets/...`). When deployed under a GitHub Pages subpath (`https://shiva-prasad-ai.github.io/code-impulse/`), absolute paths fail with 404, preventing script bundles from loading and resulting in a blank white page.
  - **Vite Config Fix:** Added `base: './'` to [`vite.config.js`](file:///d:/sthack/vite.config.js) so all script and stylesheet tags render relative paths (`./assets/index-xxxx.js`).
  - **Automated Deployment Workflow:** Created `.github/workflows/deploy.yml` to automatically build Vite, create a SPA fallback (`dist/404.html`), and deploy to GitHub Pages on every push to `main`.
  - Updated prompt log register in [`front.md`](file:///d:/sthack/front.md).

### Prompt #44 (Published Compiled Production Build to gh-pages Branch)
- **User Request:** GET https://shiva-prasad-ai.github.io/src/main.jsx net::ERR_ABORTED 404 (Not Found)
- **Action Taken:**
  - **Identified Cause:** GitHub Pages was configured to serve raw uncompiled source files from the `main` root folder instead of the compiled production build `dist`.
  - **gh-pages Integration:** Installed `gh-pages` and added `"deploy": "gh-pages -d dist"` script to [`package.json`](file:///d:/sthack/package.json).
  - **Published Production Bundle:** Executed `npm run deploy` to compile Vite assets and publish the production build directly to the `gh-pages` branch on GitHub.
### Prompt #45 (Fixing Broken Logo & Theme Toggle Assets on GitHub Pages Subpaths)
- **User Request:** i think my logo and the theme toggle button has some problem they are not pushed i think
- **Action Taken:**
  - **Identified Cause:** Hardcoded root-relative image paths (`src="/logo.png"`, `href="/logo.png"`) resolve to `https://shiva-prasad-ai.github.io/logo.png` instead of the repo subpath (`https://shiva-prasad-ai.github.io/code-impulse/logo.png`), returning 404 Not Found in live deployment.
  - **Bundled Asset Import:** Moved logo to `src/assets/logo.png` and imported `logoImg` dynamically in [`Navbar.jsx`](file:///d:/sthack/src/components/Navbar.jsx), [`ThemeToggle.jsx`](file:///d:/sthack/src/components/ThemeToggle.jsx), [`LoginPageModal.jsx`](file:///d:/sthack/src/components/LoginPageModal.jsx), [`HeroSection.jsx`](file:///d:/sthack/src/components/HeroSection.jsx), and [`PageCanvas.jsx`](file:///d:/sthack/src/components/PageCanvas.jsx).
  - **Favicon Relative Paths:** Updated `index.html` and `public/favicon.svg` to use relative asset links (`href="./favicon.svg"`, `href="logo.png"`).
  - **Production Redeployment:** Rebuilt and redeployed production build with `npm run deploy` to `gh-pages` branch and pushed updated source code to `origin/main`.
  - Updated prompt log register in [`front.md`](file:///d:/sthack/front.md).

---

## 📑 Active Tab & Page Map

| Tab ID | Tab Name | Page Status | Description |
| :--- | :--- | :--- | :--- |
| `page1` | **Page1** | 🟢 WebGPU AeroShards Active | Full-bleed WebGPU AeroShards wind sculpture background & clean hero content. |
| `page2` | **Page2** | 🟢 OGL Threads & 3 Cards Active | Interactive OGL Threads wave background + 3 cards (Teal Pulse, Green Scan, Gold Conic Spotlight buttons). |
| `page3` | **Page3** | 🟢 OGL Ferrofluid & 3 Cards Active | WebGL Ferrofluid liquid background + 3 cards (Black Stacked Shadow, Letter Squeeze, Sky Blue Glow buttons). |
| `page4` | **Page4** | 🟢 OGL WebThreads Active | Dynamic OGL WebThreads woven filament background with interactive cursor bloom & pinch point. |
| `page5` | **Page5** | 🟢 Hero Section Active | Hero section with AeroShards background & login modal. |

---

## 🏗️ Architecture & Component Tree

```
d:/sthack/
├── index.html               <-- Circular favicon & 'sthack' page title
├── package.json             <-- Added 'vgpu', 'ogl', and 'motion' dependencies
├── vite.config.js
├── front.md                 <-- Central Prompt & Component Code Register
├── public/
│   ├── favicon.svg          <-- Circular SVG favicon clipPath mask
│   ├── favicon.png          <-- Emblem favicon image
│   └── logo.png             <-- Circular eye emblem logo image
└── src/
    ├── main.jsx             <-- React entrypoint
    ├── index.css            <-- Custom button CSS rules (.btn-pulse-teal, .btn-scan-matrix, .btn-conic-spotlight, .btn-stacked-shadow, .btn-letter-squeeze, .btn-sky-glow)
    ├── App.jsx              <-- Main App container & darkMode theme state management
    └── components/
        ├── Navbar.jsx       <-- Navigation header with Login lock animation & Sign Up button
        ├── ThemeToggle.jsx  <-- Theme toggle switch with eye emblem logo knob
        ├── WifiLoader.jsx   <-- Concentric animated SVG ring loader component
        ├── HeroSection.jsx  <-- Hero section rendering AeroShards (Page1), Threads (Page2), Ferrofluid (Page3), & WebThreads (Page4)
        ├── PageCanvas.jsx   <-- Canvas page renderer with Page2, Page3, & Page4 background sections
        ├── SkeletonLoader.jsx <-- Shimmer skeleton loader page component featuring WifiLoader
        ├── LoginPageModal.jsx <-- Glassmorphic Sky & Cloud Login Page Modal
        ├── Threads/
        │   ├── Threads.jsx  <-- OGL Threads background component (Page2)
        │   └── Threads.css  <-- Threads container styling
        ├── Ferrofluid/
        │   ├── Ferrofluid.jsx <-- OGL Ferrofluid WebGL liquid component (Page3)
        │   └── Ferrofluid.css <-- Ferrofluid canvas container styling
        ├── WebThreads/
        │   ├── WebThreads.jsx <-- OGL WebThreads WebGL 2.0 woven component (Page4)
        │   └── WebThreads.css <-- WebThreads canvas container styling
        ├── SpecularButton/
        │   ├── SpecularButton.jsx <-- OGL Specular rim highlight button component
        │   └── SpecularButton.css <-- SpecularButton styles
        └── AeroShards/
            ├── AeroShards.jsx  <-- WebGPU wind-sculpture component (Page1)
            └── AeroShards.css  <-- AeroShards canvas styling
```

---

## ⚙️ How to Update `front.md` for Subsequent Prompts
1. Append new prompt entries under `📜 Full Prompt Log & History`.
2. Document new element/component/effect code snippets under `🎨 Global & Shared Component Code Registry`.
3. Update the `📑 Active Tab & Page Map` and `🏗️ Architecture & Component Tree`.
