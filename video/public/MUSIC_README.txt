To add background music to your video reels:

1. Place an MP3 file named "music.mp3" in this folder (video/public/music.mp3).
2. Open video/src/PropertyReel/PropertyReel.tsx
3. Find the commented-out <Audio> line near the bottom of PropertyReel and uncomment it:

   <Audio src={staticFile("music.mp3")} volume={0.4} />

Recommended: royalty-free instrumental background music, ~30 seconds or longer.
Resources: Pixabay (pixabay.com/music), YouTube Audio Library, Mixkit.
