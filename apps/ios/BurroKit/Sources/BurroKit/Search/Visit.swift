import Foundation

// A search is for one of three things, which the API calls its tenure: a home to rent, a
// home to buy, or somewhere to stay on a visit. A visit is a kind of search of its own. It
// holds no budget, no number of bedrooms and no kind of home, and what homes cost is no
// part of how its areas are ranked. docs/adr/0041.
//
// The record of a search has a budget in it whatever the search is for. In a visit the API
// fills it with no amount, a weight of nothing, and a kind of home that stands for nothing
// and that no client shows. So whatever draws the budget or the home of a search, asks for
// one, or holds a cost against one, asks `visiting` first.

extension PreferenceSpec {
    /// True of a search for somewhere to stay. Nothing of its budget or of its kind of
    /// home is drawn, and nothing is asked of either.
    public var visiting: Bool { tenure == .visit }
}
