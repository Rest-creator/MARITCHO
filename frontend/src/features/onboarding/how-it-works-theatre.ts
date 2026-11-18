import { getProject, types, type ISheet, type ISheetObject } from "@theatre/core";

import {
  HOW_IT_WORKS_PROJECT,
  HOW_IT_WORKS_SHEET,
  SCENE_SCRIPT,
  buildHowItWorksState,
  mapScene,
  type SceneObjectKey,
  type SceneValues,
} from "@/features/onboarding/how-it-works-script";

function sceneProps(start: SceneValues) {
  return {
    x: types.number(start.x),
    y: types.number(start.y),
    scale: types.number(start.scale, { range: [0, 2] }),
    opacity: types.number(start.opacity, { range: [0, 1] }),
    fill: types.number(start.fill, { range: [0, 1] }),
  };
}

export type SceneObject = ISheetObject<ReturnType<typeof sceneProps>>;

export interface HowItWorksRuntime {
  sheet: ISheet;
  objects: Record<SceneObjectKey, SceneObject>;
  ready: Promise<void>;
}

let runtime: HowItWorksRuntime | null = null;

/**
 * One Theatre project per page load. Theatre keeps projects and sheet objects
 * in a global registry, so re-creating them (React StrictMode remounts,
 * client navigations) must reuse this instance rather than redefine it.
 */
export function getHowItWorksRuntime(): HowItWorksRuntime {
  if (runtime !== null) return runtime;
  const project = getProject(HOW_IT_WORKS_PROJECT, { state: buildHowItWorksState() });
  const sheet: ISheet = project.sheet(HOW_IT_WORKS_SHEET);
  const objects: Record<SceneObjectKey, SceneObject> = mapScene((key) =>
    sheet.object(key, sceneProps(SCENE_SCRIPT[key].base)),
  );
  runtime = { sheet, objects, ready: project.ready };
  return runtime;
}
