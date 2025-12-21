# Remotion Guide

Remotion is a framework that can create videos programmatically.
It is based on React.js. All output should be valid React code and be written in TypeScript.

---

## Project Structure

A Remotion Project consists of an entry file, a Root file and any number of React component files.
A project can be scaffolded using the `npx create-video@latest --blank` command.

### Entry File

The entry file is usually named `src/index.ts` and looks like this:

```ts
import {registerRoot} from 'remotion';
import {Root} from './Root';

registerRoot(Root);
```

### Root File

The Root file is usually named `src/Root.tsx` and looks like this:

```tsx
import {Composition} from 'remotion';
import {MyComp} from './MyComp';

export const Root: React.FC = () => {
	return (
		<>
			<Composition
				id="MyComp"
				component={MyComp}
				durationInFrames={120}
				width={1920}
				height={1080}
				fps={30}
				defaultProps={{}}
			/>
		</>
	);
};
```

### Composition

A `<Composition>` defines a video that can be rendered. It consists of:
- A React `component`
- An `id`
- A `durationInFrames`
- A `width` and `height`
- A frame rate `fps`

**Defaults:**
- Frame rate: 30 fps
- Height: 1080px
- Width: 1920px
- ID: "MyComp"

The `defaultProps` must match the shape of the React props the `component` expects.

### Using Current Frame

Inside a React component, use the `useCurrentFrame()` hook to get the current frame number.
Frame numbers start at 0.

```tsx
export const MyComp: React.FC = () => {
	const frame = useCurrentFrame();
	return <div>Frame {frame}</div>;
};
```

---

## Component Rules

Inside a component, regular HTML and SVG tags can be returned.
There are special tags for video and audio.
Those special tags accept regular CSS styles.

### Video

If a video is included in the component it should use the `<Video>` tag:

```tsx
import {Video} from '@remotion/media';

export const MyComp: React.FC = () => {
	return (
		<div>
			<Video
				src="https://remotion.dev/bbb.mp4"
				style={{width: '100%'}}
			/>
		</div>
	);
};
```

**Video Props:**
- `trimBefore` — trims the left side of a video by a number of frames
- `trimAfter` — limits how long a video is shown
- `volume` — sets the volume (0 to 1)

### Images

If a non-animated image is included, use the `<Img>` tag:

```tsx
import {Img} from 'remotion';

export const MyComp: React.FC = () => {
	return <Img src="https://remotion.dev/logo.png" style={{width: '100%'}} />;
};
```

### Animated GIFs

For animated GIFs, install `@remotion/gif` and use the `<Gif>` tag:

```tsx
import {Gif} from '@remotion/gif';

export const MyComp: React.FC = () => {
	return (
		<Gif
			src="https://media.giphy.com/media/l0MYd5y8e1t0m/giphy.gif"
			style={{width: '100%'}}
		/>
	);
};
```

### Audio

For audio, use the `<Audio>` tag:

```tsx
import {Audio} from '@remotion/media';

export const MyComp: React.FC = () => {
	return <Audio src="https://remotion.dev/audio.mp3" />;
};
```

**Audio Props:**
- `trimBefore` — trims the left side of audio by a number of frames
- `trimAfter` — limits how long audio is played
- `volume` — sets the volume (0 to 1)

### Static Files

Asset sources can be specified as either a Remote URL or an asset referenced from the `public/` folder.
For local assets, use the `staticFile` API:

```tsx
import {staticFile} from 'remotion';
import {Audio} from '@remotion/media';

export const MyComp: React.FC = () => {
	return <Audio src={staticFile('audio.mp3')} />;
};
```

---

## Layout Components

### AbsoluteFill

To layer elements on top of each other, use `AbsoluteFill`:

```tsx
import {AbsoluteFill} from 'remotion';

export const MyComp: React.FC = () => {
	return (
		<AbsoluteFill>
			<AbsoluteFill style={{background: 'blue'}}>
				<div>This is in the back</div>
			</AbsoluteFill>
			<AbsoluteFill style={{background: 'blue'}}>
				<div>This is in front</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
```

### Sequence

Wrap elements in a `Sequence` to place them later in the video:

```tsx
import {Sequence} from 'remotion';

export const MyComp: React.FC = () => {
	return (
		<Sequence from={10} durationInFrames={20}>
			<div>This only appears after 10 frames</div>
		</Sequence>
	);
};
```

**Sequence Props:**
- `from` — frame number where the element appears (can be negative to cut off beginning)
- `durationInFrames` — how long the element appears

**Note:** If a child component of Sequence calls `useCurrentFrame()`, the enumeration starts from the first frame the Sequence appears and starts at 0.

```tsx
import {Sequence, useCurrentFrame} from 'remotion';

export const Child: React.FC = () => {
	const frame = useCurrentFrame();
	return <div>At frame 10, this should be 0: {frame}</div>;
};

export const MyComp: React.FC = () => {
	return (
		<Sequence from={10} durationInFrames={20}>
			<Child />
		</Sequence>
	);
};
```

### Series

For displaying multiple elements in sequence, use `Series`:

```tsx
import {Series} from 'remotion';

export const MyComp: React.FC = () => {
	return (
		<Series>
			<Series.Sequence durationInFrames={20}>
				<div>This appears immediately</div>
			</Series.Sequence>
			<Series.Sequence durationInFrames={30}>
				<div>This appears after 20 frames</div>
			</Series.Sequence>
			<Series.Sequence durationInFrames={30} offset={-8}>
				<div>This appears after 42 frames</div>
			</Series.Sequence>
		</Series>
	);
};
```

`Series.Sequence` works like `Sequence`, but has no `from` prop. Instead, it has an `offset` prop that shifts the start by a number of frames.

### TransitionSeries

For displaying multiple elements with transitions between them, use `TransitionSeries`:

```tsx
import {
	linearTiming,
	springTiming,
	TransitionSeries,
} from '@remotion/transitions';

import {fade} from '@remotion/transitions/fade';
import {wipe} from '@remotion/transitions/wipe';

export const MyComp: React.FC = () => {
	return (
		<TransitionSeries>
			<TransitionSeries.Sequence durationInFrames={60}>
				<Fill color="blue" />
			</TransitionSeries.Sequence>
			<TransitionSeries.Transition
				timing={springTiming({config: {damping: 200}})}
				presentation={fade()}
			/>
			<TransitionSeries.Sequence durationInFrames={60}>
				<Fill color="black" />
			</TransitionSeries.Sequence>
			<TransitionSeries.Transition
				timing={linearTiming({durationInFrames: 30})}
				presentation={wipe()}
			/>
			<TransitionSeries.Sequence durationInFrames={60}>
				<Fill color="white" />
			</TransitionSeries.Sequence>
		</TransitionSeries>
	);
};
```

**Note:** `TransitionSeries.Transition` must be placed between `TransitionSeries.Sequence` tags.

---

## Helpers & Utilities

### Random

Remotion requires all React code to be deterministic. Use the `random()` function with a static seed instead of `Math.random()`:

```tsx
import {random} from 'remotion';

export const MyComp: React.FC = () => {
	return <div>Random number: {random('my-seed')}</div>;
};
```

### Interpolate

Animate values over time with `interpolate()`:

```tsx
import {interpolate, useCurrentFrame} from 'remotion';

export const MyComp: React.FC = () => {
	const frame = useCurrentFrame();
	const value = interpolate(frame, [0, 100], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	return (
		<div>
			Frame {frame}: {value}
		</div>
	);
};
```

**Arguments:**
1. Value to animate
2. Input range array
3. Output range array
4. Options (add `extrapolateLeft: 'clamp'` and `extrapolateRight: 'clamp'` by default)

### useVideoConfig

Get composition metadata with `useVideoConfig()`:

```tsx
import {useVideoConfig} from 'remotion';

export const MyComp: React.FC = () => {
	const {fps, durationInFrames, height, width} = useVideoConfig();
	return (
		<div>
			fps: {fps}
			durationInFrames: {durationInFrames}
			height: {height}
			width: {width}
		</div>
	);
};
```

### Spring Animation

Animate values with spring physics:

```tsx
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';

export const MyComp: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	const value = spring({
		fps,
		frame,
		config: {
			damping: 200,
		},
	});
	return (
		<div>
			Frame {frame}: {value}
		</div>
	);
};
```

---

## Rendering

### Local Rendering

Render a video:

```bash
npx remotion render [id]
```

Example:

```bash
npx remotion render MyComp
```

Render a still image:

```bash
npx remotion still [id]
```

Example:

```bash
npx remotion still MyComp
```

### Rendering on Lambda

Videos can be rendered in the cloud using AWS Lambda.
Complete the setup at https://www.remotion.dev/docs/lambda/setup first.

Rendering requires a Lambda function and a site deployed on S3.

**Using CLI:**

1. Deploy a Lambda function:
   ```bash
   npx remotion lambda functions deploy
   ```
   See: https://www.remotion.dev/docs/lambda/cli/functions/deploy

2. Deploy a site:
   ```bash
   npx remotion lambda sites create [entry-point]
   ```
   See: https://www.remotion.dev/docs/lambda/cli/sites/create

3. Render a video:
   ```bash
   npx remotion lambda render [comp-id]
   ```

**Using Node.js APIs:**

- Deploy function: `deployFunction()` — https://www.remotion.dev/docs/lambda/deployfunction
- Deploy site: `deploySite()` — https://www.remotion.dev/docs/lambda/deploysite
- Render video: `renderMediaOnLambda()` — https://www.remotion.dev/docs/lambda/rendermediaonlambda
- Poll progress: `getRenderProgress()` — https://www.remotion.dev/docs/lambda/getrenderprogress

---

## @remotion/player

Using the Remotion Player you can embed Remotion videos in any React app and customize the video content at runtime.

### Templates

The following templates include the Player and Lambda rendering and are a good starting point for building a video app:

- [Next.js (App dir)](https://www.remotion.dev/templates/next)
- [Next.js (App dir + TailwindCSS)](https://www.remotion.dev/templates/next-tailwind)
- [Next.js (Pages dir)](https://www.remotion.dev/templates/next-pages-dir)
- [React Router 7 (Remix)](https://www.remotion.dev/templates/react-router)

### Resources

- [Installation](https://www.remotion.dev/docs/player/installation)
- [API Reference](https://www.remotion.dev/docs/player/player)
- [Demo & Examples](https://github.com/remotion-dev/remotion/blob/main/packages/docs/components/PlayerExampleWithControls.tsx)

