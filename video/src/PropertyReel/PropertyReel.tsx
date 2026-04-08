import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Series,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ── Constants ─────────────────────────────────────────────────
export const PHOTO_DURATION = 110; // frames per photo  (~3.7 sec @ 30fps)
export const CONTACT_DURATION = 150; // frames for contact screen (~5 sec)

const BLUE = "#1B4F8A";
const GREEN = "#27AE60";
const WHITE = "#FFFFFF";

// ── Types ─────────────────────────────────────────────────────
export interface ReelProps {
  photos: string[];
  price: number;
  city: string;
  state: string;
  bedrooms: number;
  bathrooms: number;
  built_area: number;
  operation: string;
  agentName: string;
  agentPhone: string;
  agentEmail: string;
}

// ── Photo segment with Ken Burns ──────────────────────────────
const PhotoSegment: React.FC<{
  photo: string;
  overlay: React.ReactNode;
  duration: number;
}> = ({ photo, overlay, duration }) => {
  const frame = useCurrentFrame();

  const scale = interpolate(frame, [0, duration], [1.0, 1.08], {
    extrapolateRight: "clamp",
  });

  const opacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      {/* Photo with Ken Burns zoom */}
      <AbsoluteFill style={{ overflow: "hidden" }}>
        <Img
          src={staticFile(photo)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${scale})`,
            transformOrigin: "center center",
          }}
        />
      </AbsoluteFill>

      {/* Gradient overlay */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, transparent 25%, rgba(0,0,0,0.80) 100%)",
        }}
      />

      {overlay}
    </AbsoluteFill>
  );
};

// ── Price overlay (photo 0) ───────────────────────────────────
const PriceOverlay: React.FC<{
  price: number;
  operation: string;
}> = ({ price, operation }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isForSale = operation.toLowerCase() === "sale";

  const ty = spring({ frame: frame - 20, fps, config: { damping: 200 }, from: 60, to: 0 });
  const opacity = interpolate(frame, [20, 36], [0, 1], { extrapolateRight: "clamp" });

  const formatted = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(price);

  return (
    <AbsoluteFill
      style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 200 }}
    >
      <div
        style={{
          opacity,
          transform: `translateY(${ty}px)`,
          textAlign: "center",
          padding: "0 40px",
        }}
      >
        <div
          style={{
            display: "inline-block",
            background: isForSale ? BLUE : GREEN,
            color: WHITE,
            padding: "14px 36px",
            borderRadius: 10,
            fontSize: 40,
            fontWeight: 700,
            fontFamily: "Helvetica Neue, Arial, sans-serif",
            marginBottom: 24,
            letterSpacing: 3,
          }}
        >
          {isForSale ? "FOR SALE" : "FOR RENT"}
        </div>
        <div
          style={{
            fontSize: 110,
            fontWeight: 900,
            color: WHITE,
            fontFamily: "Helvetica Neue, Arial, sans-serif",
            textShadow: "0 4px 24px rgba(0,0,0,0.55)",
            lineHeight: 1,
          }}
        >
          {formatted}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Location overlay (photo 1) ────────────────────────────────
const LocationOverlay: React.FC<{ city: string; state: string }> = ({ city, state }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const ty = spring({ frame: frame - 15, fps, config: { damping: 200 }, from: 50, to: 0 });
  const opacity = interpolate(frame, [15, 30], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 220 }}
    >
      <div style={{ opacity, transform: `translateY(${ty}px)`, textAlign: "center" }}>
        <div
          style={{
            fontSize: 90,
            fontWeight: 700,
            color: WHITE,
            fontFamily: "Helvetica Neue, Arial, sans-serif",
            textShadow: "0 3px 18px rgba(0,0,0,0.6)",
            lineHeight: 1.15,
          }}
        >
          {city}
        </div>
        <div
          style={{
            fontSize: 64,
            fontWeight: 400,
            color: "rgba(255,255,255,0.88)",
            fontFamily: "Helvetica Neue, Arial, sans-serif",
            textShadow: "0 2px 12px rgba(0,0,0,0.5)",
            marginTop: 8,
          }}
        >
          {state}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Details overlay (photo 2) ─────────────────────────────────
const DetailsOverlay: React.FC<{
  bedrooms: number;
  bathrooms: number;
  built_area: number;
}> = ({ bedrooms, bathrooms, built_area }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({ frame: frame - 15, fps, config: { damping: 200 }, from: 0.8, to: 1.0 });
  const opacity = interpolate(frame, [15, 30], [0, 1], { extrapolateRight: "clamp" });

  const area = new Intl.NumberFormat("en-US").format(built_area);

  return (
    <AbsoluteFill
      style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 220 }}
    >
      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
          textAlign: "center",
          background: "rgba(0,0,0,0.58)",
          borderRadius: 22,
          padding: "36px 64px",
        }}
      >
        <div
          style={{
            fontSize: 78,
            fontWeight: 700,
            color: WHITE,
            fontFamily: "Helvetica Neue, Arial, sans-serif",
            letterSpacing: 2,
          }}
        >
          {bedrooms} Beds · {bathrooms} Baths
        </div>
        <div
          style={{
            fontSize: 56,
            color: "rgba(255,255,255,0.85)",
            fontFamily: "Helvetica Neue, Arial, sans-serif",
            marginTop: 14,
          }}
        >
          {area} sq ft
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── CTA overlay (photo 3+) ────────────────────────────────────
const CTAOverlay: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const ty = spring({ frame: frame - 15, fps, config: { damping: 200 }, from: 40, to: 0 });
  const opacity = interpolate(frame, [15, 30], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 240 }}
    >
      <div
        style={{
          opacity,
          transform: `translateY(${ty}px)`,
          background: "rgba(27, 79, 138, 0.88)",
          padding: "28px 54px",
          borderRadius: 18,
        }}
      >
        <div
          style={{
            fontSize: 66,
            fontWeight: 700,
            color: WHITE,
            fontFamily: "Helvetica Neue, Arial, sans-serif",
            textAlign: "center",
          }}
        >
          Schedule a Visit Today
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Contact screen (final segment) ───────────────────────────
const ContactScreen: React.FC<{
  agentName: string;
  agentPhone: string;
  agentEmail: string;
}> = ({ agentName, agentPhone, agentEmail }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoOpacity = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: "clamp" });

  const nameY = spring({ frame: frame - 28, fps, config: { damping: 200 }, from: 40, to: 0 });
  const nameOpacity = interpolate(frame, [28, 48], [0, 1], { extrapolateRight: "clamp" });

  const phoneY = spring({ frame: frame - 50, fps, config: { damping: 200 }, from: 40, to: 0 });
  const phoneOpacity = interpolate(frame, [50, 68], [0, 1], { extrapolateRight: "clamp" });

  const emailY = spring({ frame: frame - 70, fps, config: { damping: 200 }, from: 40, to: 0 });
  const emailOpacity = interpolate(frame, [70, 88], [0, 1], { extrapolateRight: "clamp" });

  const taglineOpacity = interpolate(frame, [92, 112], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: BLUE,
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        gap: 28,
      }}
    >
      {/* ListPro wordmark */}
      <div style={{ opacity: logoOpacity, textAlign: "center", marginBottom: 44 }}>
        <div
          style={{
            fontSize: 128,
            fontWeight: 900,
            color: WHITE,
            fontFamily: "Helvetica Neue, Arial, sans-serif",
            letterSpacing: 4,
          }}
        >
          ListPro
        </div>
        <div
          style={{
            width: 130,
            height: 7,
            background: GREEN,
            borderRadius: 4,
            margin: "14px auto 0",
          }}
        />
      </div>

      {/* Agent name */}
      <div
        style={{
          opacity: nameOpacity,
          transform: `translateY(${nameY}px)`,
          fontSize: 76,
          fontWeight: 700,
          color: WHITE,
          fontFamily: "Helvetica Neue, Arial, sans-serif",
          textAlign: "center",
          padding: "0 60px",
        }}
      >
        {agentName}
      </div>

      {/* Phone */}
      <div
        style={{
          opacity: phoneOpacity,
          transform: `translateY(${phoneY}px)`,
          fontSize: 58,
          color: "rgba(255,255,255,0.85)",
          fontFamily: "Helvetica Neue, Arial, sans-serif",
          textAlign: "center",
        }}
      >
        {agentPhone}
      </div>

      {/* Email */}
      <div
        style={{
          opacity: emailOpacity,
          transform: `translateY(${emailY}px)`,
          fontSize: 48,
          color: "rgba(255,255,255,0.72)",
          fontFamily: "Helvetica Neue, Arial, sans-serif",
          textAlign: "center",
          padding: "0 40px",
        }}
      >
        {agentEmail}
      </div>

      {/* Tagline */}
      <div
        style={{
          position: "absolute",
          bottom: 90,
          opacity: taglineOpacity,
          fontSize: 34,
          color: "rgba(255,255,255,0.48)",
          fontFamily: "Helvetica Neue, Arial, sans-serif",
          textAlign: "center",
          letterSpacing: 4,
          textTransform: "uppercase",
        }}
      >
        AI-Powered Real Estate
      </div>
    </AbsoluteFill>
  );
};

// ── Root composition ──────────────────────────────────────────
export const PropertyReel: React.FC<ReelProps> = (props) => {
  const {
    photos,
    price,
    city,
    state,
    bedrooms,
    bathrooms,
    built_area,
    operation,
    agentName,
    agentPhone,
    agentEmail,
  } = props;

  const displayPhotos = (photos ?? []).slice(0, 5);

  const overlays: React.ReactNode[] = [
    <PriceOverlay key="price" price={price} operation={operation} />,
    <LocationOverlay key="loc" city={city} state={state} />,
    <DetailsOverlay key="det" bedrooms={bedrooms} bathrooms={bathrooms} built_area={built_area} />,
    <CTAOverlay key="cta0" />,
    <CTAOverlay key="cta1" />,
  ];

  // If no photos were provided, skip to contact screen only
  if (displayPhotos.length === 0) {
    return (
      <AbsoluteFill>
        <ContactScreen agentName={agentName} agentPhone={agentPhone} agentEmail={agentEmail} />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill>
      <Series>
        {displayPhotos.map((photo, i) => (
          <Series.Sequence key={photo + i} durationInFrames={PHOTO_DURATION}>
            <PhotoSegment
              photo={photo}
              overlay={overlays[i] ?? <CTAOverlay key={`extra-${i}`} />}
              duration={PHOTO_DURATION}
            />
          </Series.Sequence>
        ))}

        <Series.Sequence durationInFrames={CONTACT_DURATION}>
          <ContactScreen
            agentName={agentName}
            agentPhone={agentPhone}
            agentEmail={agentEmail}
          />
        </Series.Sequence>
      </Series>

      <Audio src={staticFile("music.mp3")} volume={0.15} />
    </AbsoluteFill>
  );
};
