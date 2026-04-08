import React from "react";
import { Composition } from "remotion";
import { PropertyReel, PHOTO_DURATION, CONTACT_DURATION } from "./PropertyReel/PropertyReel";
import type { ReelProps } from "./PropertyReel/PropertyReel";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="PropertyReel"
      component={PropertyReel}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        photos: [],
        price: 450000,
        city: "Austin",
        state: "TX",
        bedrooms: 3,
        bathrooms: 2,
        built_area: 2000,
        operation: "Sale",
        agentName: "Jane Smith",
        agentPhone: "(512) 555-0100",
        agentEmail: "jane@realty.com",
      } as ReelProps}
      calculateMetadata={async ({ props }) => {
        const photoCount = Math.max(1, Math.min((props.photos?.length ?? 0), 5));
        return {
          durationInFrames: photoCount * PHOTO_DURATION + CONTACT_DURATION,
        };
      }}
    />
  );
};
