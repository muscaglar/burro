/**
 * How long a test waits for the page before it gives up.
 *
 * A wait that is too short fails on a slow machine and passes on a fast one, which says
 * nothing about the page. The library allows one second. The field for a place spends a
 * quarter of that before it asks, and the page is then found again by its roles, which
 * jsdom is slow at.
 */

import { getConfig } from "@testing-library/dom";

import { WAIT_MS } from "@/components/PlaceCombobox/PlaceCombobox";

describe("how long a test waits", () => {
  test("test_a_wait_for_the_page_leaves_room_for_a_machine_many_times_slower", () => {
    // What is left of a wait once the field has asked is for the page to be drawn and found.
    expect(getConfig().asyncUtilTimeout - WAIT_MS).toBeGreaterThanOrEqual(4_000);
  });
});
