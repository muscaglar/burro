import { pass } from "@/lib/account/pass";

/**
 * The website stands between the browser and the service for the routes of accounts:
 * `lib/account/pass.ts` has the whole of it. Every method is answered by it, so that what
 * is no route of its list is answered the same whatever was asked, and nothing is
 * answered for it by the framework.
 *
 * It is asked for each time, and nothing of an answer is kept.
 */
export const dynamic = "force-dynamic";

const passOn = (request: Request): Promise<Response> => pass(request);

export {
  passOn as DELETE,
  passOn as GET,
  passOn as HEAD,
  passOn as OPTIONS,
  passOn as PATCH,
  passOn as POST,
  passOn as PUT,
};
