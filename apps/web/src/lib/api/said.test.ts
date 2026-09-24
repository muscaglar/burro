import { disagrees, forgetWhatWasSaid, noteSaid, NOTHING_SAID, subscribeToWhatWasSaid, whatWasSaid } from "./said";

const MADE_UP = { synthetic: true, preview: false };
const REAL_PREVIEW = { synthetic: false, preview: true };
const FINISHED = { synthetic: false, preview: false };

beforeEach(forgetWhatWasSaid);

describe("what the answers have said of their data", () => {
  test("test_before_any_answer_nothing_has_been_said", () => {
    expect(whatWasSaid()).toEqual(NOTHING_SAID);
    expect(whatWasSaid()).toEqual({ madeUp: false, real: false, preview: false, finished: false });
  });

  test("test_each_answer_is_heard_and_nothing_heard_is_forgotten", () => {
    noteSaid(MADE_UP);
    expect(whatWasSaid()).toEqual({ madeUp: true, real: false, preview: false, finished: true });

    noteSaid(REAL_PREVIEW);
    expect(whatWasSaid()).toEqual({ madeUp: true, real: true, preview: true, finished: true });
  });

  test("test_an_answer_that_says_nothing_of_one_flag_leaves_it_as_it_was", () => {
    noteSaid({ synthetic: null, preview: true });
    expect(whatWasSaid()).toEqual({ madeUp: false, real: false, preview: true, finished: false });
  });

  test("test_whoever_listens_is_told_when_something_new_is_said_and_only_then", () => {
    const told = jest.fn();
    const stop = subscribeToWhatWasSaid(told);

    noteSaid(MADE_UP);
    noteSaid(MADE_UP);
    expect(told).toHaveBeenCalledTimes(1);
    const before = whatWasSaid();
    noteSaid(MADE_UP);
    // The same thing is given while nothing new is said, so that a page is not drawn again.
    expect(whatWasSaid()).toBe(before);

    stop();
    noteSaid(REAL_PREVIEW);
    expect(told).toHaveBeenCalledTimes(1);
  });
});

describe("whether an answer is of another kind of data than the page was built on", () => {
  test("test_a_page_and_answers_of_the_same_kind_agree", () => {
    noteSaid(MADE_UP);
    expect(disagrees(MADE_UP, whatWasSaid())).toBe(false);
    expect(disagrees(REAL_PREVIEW, NOTHING_SAID)).toBe(false);
  });

  test("test_a_page_built_on_made_up_data_disagrees_with_an_answer_that_is_real", () => {
    noteSaid(REAL_PREVIEW);
    expect(disagrees(MADE_UP, whatWasSaid())).toBe(true);
  });

  test("test_a_page_built_on_real_data_disagrees_with_an_answer_that_is_made_up", () => {
    noteSaid(MADE_UP);
    expect(disagrees(FINISHED, whatWasSaid())).toBe(true);
  });

  test("test_a_page_built_on_a_finished_release_disagrees_with_an_answer_of_a_preview", () => {
    noteSaid(REAL_PREVIEW);
    expect(disagrees(FINISHED, whatWasSaid())).toBe(true);
  });

  test("test_a_page_built_on_a_preview_disagrees_with_an_answer_of_a_finished_release", () => {
    noteSaid(FINISHED);
    expect(disagrees(REAL_PREVIEW, whatWasSaid())).toBe(true);
  });
});
