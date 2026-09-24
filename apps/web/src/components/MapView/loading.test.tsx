import { render } from "@testing-library/react";

import { recordedAnswer } from "@/lib/api/recorded";

import { arrived, setWebGL } from "../../../test/support/search";
import { MapView } from "./MapView";

const loaded = { times: 0 };

// The map library, as the page loads it: on demand. Loading it is counted here.
jest.mock("@/lib/map/library", () => {
  loaded.times += 1;
  return jest.requireActual<typeof import("../../../test/support/maplibre")>(
    "../../../test/support/maplibre",
  );
});

const geometry = recordedAnswer("get_geometry", "geometry").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;

async function show() {
  render(
    <MapView
      geometry={geometry}
      areas={areas}
      scores={[]}
      ranked={[]}
      filtered={[]}
      unranked={[]}
      selectedId={null}
      hoveredId={null}
      onSelect={() => undefined}
      onHover={() => undefined}
      onShowInList={() => undefined}
      table={null}
    />,
  );
  await arrived();
}

describe("when the map library is loaded", () => {
  afterEach(() => setWebGL(false));

  test("test_without_webgl_the_map_library_is_never_loaded", async () => {
    setWebGL(false);

    await show();

    expect(loaded.times).toBe(0);
  });

  test("test_with_webgl_the_map_library_is_loaded_when_the_map_is_shown", async () => {
    setWebGL(true);

    await show();

    expect(loaded.times).toBe(1);
  });
});
