/**
 * The browser a component is tested in: jsdom, with the three classes of
 * `fetch` that jsdom leaves out. They are Node's own. `fetch` itself is not
 * handed over: tests run offline, and jest.setup.ts says so to any test that
 * calls it without a stand-in.
 */

import JSDOMEnvironment from "jest-environment-jsdom";

export default class Environment extends JSDOMEnvironment {
  constructor(...args: ConstructorParameters<typeof JSDOMEnvironment>) {
    super(...args);
    Object.assign(this.global, { Headers, Request, Response });
  }
}
