# X Agent Factory Dashboard (Phase 3)

## Overview
This is the "Factory Floor" UI for the X Agent Factory. It serves two purposes:
1.  **Management Console**: View active opportunities and agent build status.
2.  **Interactive Demo Environment**: Test agents in a live context using the "Agent-First" layout.

## Tech Stack
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Integration**: Tavus (Video), Gemini (Logic)

## Key Features
- **Global Sidebar**: A fixed right-hand sidebar (`w-[500px]`) that persists across the application, simulating the "Agent Overlay" experience.
- **Iframe Scaler**: The `/demo` route includes a logic to scale client websites (0.55x) to fit within the remaining viewport without horizontal scrolling issues.

## Usage
- Run Dev Server: `npm run dev`
- Visit `http://localhost:3000` for the Pipeline View.
- Visit `http://localhost:3000/demo` for the Interactive Demo.
