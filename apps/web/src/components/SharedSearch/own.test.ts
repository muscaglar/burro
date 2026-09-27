import { GOOD_FOR_MS, takeTheWay, wasTaken } from "./own";

describe("the mark that the way to a search of one's own was pressed", () => {
  afterEach(() => {
    jest.restoreAllMocks();
    wasTaken();
  });

  test("test_it_is_read_once_and_is_then_gone", () => {
    expect(wasTaken()).toBe(false);

    takeTheWay();

    expect(wasTaken()).toBe(true);
    expect(wasTaken()).toBe(false);
  });

  test("test_a_press_that_led_nowhere_begins_nothing_again_when_the_page_is_left_later", () => {
    const clock = jest.spyOn(performance, "now");
    clock.mockReturnValue(1_000);
    takeTheWay();

    clock.mockReturnValue(1_000 + GOOD_FOR_MS + 1);

    expect(wasTaken()).toBe(false);
    // And it is gone for good, however the clock stands.
    clock.mockReturnValue(1_001);
    expect(wasTaken()).toBe(false);
  });

  test("test_it_is_good_for_as_long_as_a_page_may_take_to_come", () => {
    const clock = jest.spyOn(performance, "now");
    clock.mockReturnValue(5_000);
    takeTheWay();

    clock.mockReturnValue(5_000 + GOOD_FOR_MS);

    expect(wasTaken()).toBe(true);
  });
});
