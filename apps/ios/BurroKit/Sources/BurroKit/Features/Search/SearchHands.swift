import Foundation

// What a press on the search screen does. Each is one call to what the shell
// and the search hand to a feature, so that a press is tested with no screen.
//
// A sentence is handed to the one call that sends it, and is kept nowhere
// here. "Try again" is given the sentence again by the box, because none is kept.

@MainActor
struct SearchHands {
    let app: AppModel
    let search: SearchStore

    /// Sends the one edit of a control.
    func send(_ operations: Operations) async {
        await search.flow.applyEdits(operations)
    }

    func chooseTenure(_ tenure: Tenure) async {
        await search.flow.setTenure(tenure)
    }

    /// Sends a sentence to be read, and goes to the results when there is nothing here to read first.
    func submit(_ text: String) async {
        let before = search.state.answers
        await search.flow.submitText(text)
        arrive(since: before)
    }

    /// Takes one choice of a thing Burro noticed, by the id of the choice. Nothing is
    /// ranked from it until now. A journey to a place Burro does not know comes with
    /// the place the person chose for it.
    func choose(_ at: Int, _ id: String, place: (id: String, name: String)? = nil) async {
        let before = search.state.answers
        await search.flow.choose(at: at, id: id, place: place)
        arrive(since: before)
    }

    /// Takes the one way of each of these things, all at once.
    func chooseAll(_ ats: [Int]) async {
        let before = search.state.answers
        await search.flow.chooseAll(ats)
        arrive(since: before)
    }

    /// Takes back all that the last press of "Add all" added. The offers are as they
    /// were, so the person stays here to choose of them.
    func takeBack() async {
        await search.flow.takeBack()
    }

    /// Ranks the settings as they stand, with no words.
    func rankNow() async {
        let before = search.state.answers
        await search.flow.rankNow()
        arrive(since: before)
    }

    /// Tries again what failed. The sentence is the one that is in the box.
    func tryAgain(_ text: String) async {
        let before = search.state.answers
        await search.flow.retry(text: text)
        arrive(since: before)
    }

    /// The phone may be online again. The change that waited is sent once,
    /// and a sentence that could not leave is sent again from the box.
    func comeBack(_ text: String) async {
        let step = search.state.failedStep
        await search.flow.wentOnline()
        if step == .read, !PromptText.isEmpty(text) { await submit(text) }
    }

    /// Goes to the list and the map.
    func showResults() {
        app.show(.results, in: .search)
    }

    /// Goes to the list and the map, when a ranking has just come and nothing
    /// here needs reading first.
    private func arrive(since before: Int) {
        let onTop = app.tab == .search && app.searchPath.isEmpty
        if SearchScreen.arrives(search.state, since: before, onTop: onTop) {
            showResults()
        }
    }
}
