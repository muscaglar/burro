import { render } from "@testing-library/react";

import { faultsIn } from "./axe";

describe("the accessibility check itself", () => {
  test("test_the_check_finds_a_fault_where_there_is_one", async () => {
    const { container } = render(
      <div>
        {/* eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text */}
        <img src="data:," />
        <button type="button" />
        <input type="text" />
        <table>
          <tbody>
            <tr>
              <td headers="nothing-has-this-id">A cell</td>
            </tr>
          </tbody>
        </table>
      </div>,
    );

    const faults = await faultsIn(container);

    expect(faults.map((fault) => fault.split(":")[0]).sort()).toEqual([
      "button-name",
      "image-alt",
      "label",
      "td-headers-attr",
    ]);
  });

  test("test_a_whole_page_is_held_to_more_than_a_part_of_one", async () => {
    const { container } = render(<p>Words outside any landmark.</p>);

    expect(await faultsIn(container)).toEqual([]);
    expect((await faultsIn(container, { wholePage: true })).join(" ")).toContain("region");
  });
});
