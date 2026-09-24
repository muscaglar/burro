# The iOS app. `make check` says whether it is sound. `make help` lists the targets.
# Needs a Mac with Xcode that can run `swift test`, and python3. Nothing is installed from a package.

.DEFAULT_GOAL := help
.PHONY: help check generate generate-check test build clean

DERIVED := build/DerivedData
# For any iPhone and signed by nobody, so it needs no team and no simulator.
XCODEBUILD := xcodebuild -project Burro.xcodeproj -scheme Burro \
	-destination 'generic/platform=iOS' -derivedDataPath $(DERIVED) \
	-quiet CODE_SIGNING_ALLOWED=NO

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | expand -t 18

check: generate-check test build ## Everything: run this before you say you are done

generate: ## Write the API models, the tokens and the recorded answers from their sources
	python3 scripts/generate.py

generate-check: ## Fail if anything generated is out of date
	python3 scripts/generate.py --check

test: ## Run the package's tests on macOS. One class or test: make test ONLY=ReduceTests
	swift test --package-path BurroKit -Xswiftc -warnings-as-errors $(if $(ONLY),--filter $(ONLY))

build: ## Compile the app for iOS, in Debug and in Release, with code signing off
	$(XCODEBUILD) -configuration Debug build
	$(XCODEBUILD) -configuration Release build
	test -f $(DERIVED)/Build/Products/Debug-iphoneos/Burro.app/PrivacyInfo.xcprivacy
	test -f $(DERIVED)/Build/Products/Release-iphoneos/Burro.app/PrivacyInfo.xcprivacy

clean: ## Remove what a build leaves behind
	rm -rf build BurroKit/.build
