import SwiftUI

/// The first screen of the Search tab: the box to type in, renting or buying,
/// a place to reach, what Burro understood, and the settings that do the same
/// job as a form.
///
/// It is drawn inside `Opened`, so the search is in the environment. It reads
/// `search.state` and asks `search.flow` to do things. It goes to the results
/// with `app.show(.results)`.
///
/// It decides nothing of what it shows: `SearchScreen.shown` does, and this
/// draws each part in the order that gives.
public struct SearchRootView: View {
    @Environment(AppModel.self) private var app
    @Environment(SearchStore.self) private var search
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    /// What is in the box. It is held here, while the screen is open, so that
    /// "Try again" can send it again. It goes nowhere else.
    @State private var words = ""
    @State private var examplesOpen = true

    public init() {}

    public var body: some View {
        let state = search.state
        let shown = SearchScreen.shown(state, consent: app.consent.choice)
        let context = ControlContext(state: state, send: { send($0) })
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Space.s5) {
                ForEach(shown.parts, id: \.self) { part in
                    draw(part, shown, context)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(Tokens.Space.gutter)
        }
        .background(Tokens.Colour.bg)
        .navigationTitle(ShellCopy.title(of: .search))
        .scrollDismissesKeyboard(.interactively)
        .onChange(of: shown.status) { _, status in
            Spoken.say(status)
        }
        .task(id: app.consent.choice) {
            if SearchScreen.opensTheForm(search.state, consent: app.consent.choice) {
                search.flow.openSettings(true)
            }
        }
        .onChange(of: scenePhase) { _, phase in
            // Nothing tells the app that the phone is online again. Coming back
            // to the app is a fair moment to send what was waiting.
            if phase == .active, !search.state.online { comeBack() }
        }
    }

    // MARK: - The parts

    @ViewBuilder
    private func draw(_ part: SearchPart, _ shown: SearchShown, _ context: ControlContext) -> some View {
        switch part {
        case .box: box(shown)
        case .examples: examples
        case .basics: basics(shown, context)
        case .status: status(shown)
        case .offline: OfflineBlock(waiting: shown.offlineWaiting ?? false, tryAgain: comeBack)
        case .couldNotRead: couldNotRead(shown)
        case .failure: failure(shown)
        case .notice: notice(shown)
        case .nothingRead: nothingRead(shown)
        case .questions: questions(shown)
        case .chips: chips(shown, context)
        case .unmet: unmet(shown)
        case .notApplied: notApplied(shown)
        case .results: results
        case .settings: settings(shown, context)
        }
    }

    @ViewBuilder
    private func box(_ shown: SearchShown) -> some View {
        switch shown.box {
        case .offered:
            VStack(alignment: .leading, spacing: Tokens.Space.s3) {
                PromptBox(
                    text: $words,
                    maxText: search.state.meta.limits.maxText,
                    busy: shown.reading,
                    refusal: shown.boxProblem,
                    onSubmit: { text in
                        examplesOpen = false
                        Task { await hands.submit(text) }
                    },
                    onStop: { Task { await search.flow.stop() } })
                HintLine(SearchCopy.Permission.handled)
                NavigationLink(value: Screen.methods) {
                    Text(SearchCopy.Prompt.wordsLink)
                        .font(Tokens.Text.secondary)
                        .underline()
                        .frame(minHeight: Tokens.Target.least, alignment: .leading)
                        .contentShape(Rectangle())
                }
            }
        case .declined:
            DeclinedLine { app.showRoot(of: .about) }
        }
    }

    private var examples: some View {
        ExampleList(open: $examplesOpen) { sentence in
            words = sentence
        }
    }

    private func basics(_ shown: SearchShown, _ context: ControlContext) -> some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s4) {
            TenureControl(
                tenure: context.spec.tenure, version: context.version, problem: nil,
                choose: chooseTenure)
            PlaceField(full: shown.placesFull, search: searchPlaces) { place in
                Task { await search.flow.addPlace(place) }
            }
        }
    }

    @ViewBuilder
    private func status(_ shown: SearchShown) -> some View {
        let turning = SearchScreen.showsItIsBusy(shown, reduceMotion: reduceMotion)
        if !shown.status.isEmpty || turning {
            HStack(alignment: .center, spacing: Tokens.Space.s2) {
                if turning {
                    // The words say what is happening. The mark repeats it.
                    ProgressView()
                        .accessibilityHidden(true)
                }
                Text(shown.status)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.muted)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private func couldNotRead(_ shown: SearchShown) -> some View {
        let again: (() -> Void)? = shown.couldNotReadRetry == true ? { tryAgain() } : nil
        return CouldNotReadBlock(tryAgain: again)
    }

    @ViewBuilder
    private func failure(_ shown: SearchShown) -> some View {
        if let failure = shown.failure {
            SearchErrorBlock(
                failure: failure,
                repair: { send($0) },
                tryAgain: { tryAgain() },
                startAgain: { search.flow.startAgain() })
        }
    }

    @ViewBuilder
    private func notice(_ shown: SearchShown) -> some View {
        if let notice = shown.notice { NoticeBlock(text: notice) }
    }

    @ViewBuilder
    private func nothingRead(_ shown: SearchShown) -> some View {
        if let line = shown.nothingRead { StateLine(line) }
    }

    private func questions(_ shown: SearchShown) -> some View {
        ForEach(shown.questions) { question in
            QuestionBlock(
                question: question,
                search: searchPlaces,
                pick: { id, name in
                    Task { await search.flow.answerClarify(question.asked, id: id, name: name) }
                },
                leaveOut: { search.flow.leaveOut(question.asked) })
        }
    }

    private func chips(_ shown: SearchShown, _ context: ControlContext) -> some View {
        ChipList(
            title: shown.chipsTitle, chips: shown.chips, waiting: shown.chipsWaiting,
            hints: shown.chipsHints, context: context,
            chooseTenure: { chooseTenure($0) },
            openSettings: { search.flow.openSettings(true) })
    }

    private func unmet(_ shown: SearchShown) -> some View {
        LineList(
            label: SearchCopy.Notice.unmetLabel,
            lines: shown.unmet.map { LineList.Line(about: nil, words: $0) })
    }

    private func notApplied(_ shown: SearchShown) -> some View {
        LineList(
            label: SearchCopy.Notice.rejectedLabel,
            lines: shown.notApplied.map { LineList.Line(about: $0.about, words: $0.reason) })
    }

    private var results: some View {
        Button(SearchCopy.Status.showResults) {
            hands.showResults()
        }
        .buttonStyle(.burroSecondary)
    }

    private func settings(_ shown: SearchShown, _ context: ControlContext) -> some View {
        let rank: (() -> Void)? = shown.canRank ? { rankNow() } : nil
        return SettingsPanel(
            context: context,
            open: shown.settingsOpen,
            setOpen: { search.flow.openSettings($0) },
            rank: rank)
    }

    // MARK: - What a person can do

    private var hands: SearchHands {
        SearchHands(app: app, search: search)
    }

    private var searchPlaces: @MainActor (String) async -> Answer<PlacesData> {
        let flow = search.flow
        return { text in await flow.searchPlaces(text) }
    }

    private func send(_ operations: Operations) {
        Task { await hands.send(operations) }
    }

    private func chooseTenure(_ tenure: Tenure) {
        Task { await hands.chooseTenure(tenure) }
    }

    private func rankNow() {
        Task { await hands.rankNow() }
    }

    private func tryAgain() {
        let text = words
        Task { await hands.tryAgain(text) }
    }

    private func comeBack() {
        let text = words
        Task { await hands.comeBack(text) }
    }
}
