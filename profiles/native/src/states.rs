//! Generated from profiles/native/states.json. Do not edit.
//!
//! The states the system's elements declare, as a native target reads
//! them: what a state means, the role it wears, and the treatment a
//! surface gives it. The structure does not cross the boundary; the
//! meaning and the state do.

#![allow(dead_code)]

/// One state: what it means, and the role it wears when it wears one.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct State {
    pub id: &'static str,
    pub role: Option<&'static str>,
    pub treatment: &'static str,
    pub evidence: &'static str,
}

/// The state a thing is in when nothing has happened to it.
pub const DEFAULT: State = State {
    id: "default",
    role: None,
    treatment: "The element's own surface and its own type, and nothing else.",
    evidence: "A capture of the resting surface, on both substrates.",
};

/// The pointer is over the thing.
pub const HOVER: State = State {
    id: "hover",
    role: None,
    treatment: "A surface treatment that the pointer leaving takes back, and that never pretends to be focus.",
    evidence: "A pointer capture, and a keyboard traversal that shows the two are different.",
};

/// The keyboard is on the thing.
pub const FOCUS_VISIBLE: State = State {
    id: "focus-visible",
    role: Some("focus"),
    treatment: "An explicit visible focus treatment, independent of hover, and readable against the surface it sits on.",
    evidence: "A keyboard traversal capture, and the contrast of the focus treatment against that surface.",
};

/// The thing is being pressed.
pub const ACTIVE: State = State {
    id: "active",
    role: None,
    treatment: "A pressed surface, distinct from focus, and a pointer that says it.",
    evidence: "A press capture, and the keyboard equivalent where the thing has one.",
};

/// The thing cannot be acted on.
pub const DISABLED: State = State {
    id: "disabled",
    role: None,
    treatment: "A surface that reads as unavailable without relying on colour alone, and a pointer that says so.",
    evidence: "A capture of the disabled surface, and a pointer check.",
};

/// The thing is working, and the work is not finished.
pub const BUSY: State = State {
    id: "busy",
    role: None,
    treatment: "A progress indication that expresses the wait and never resolves it: the state stays pending until an observation reports a result.",
    evidence: "A pending capture, and a check that the pending state is not the observed one.",
};

/// The thing is showing what it holds.
pub const OPEN: State = State {
    id: "open",
    role: None,
    treatment: "An overlay above the surface that opened it, which takes the keyboard while it is open.",
    evidence: "A capture of the open state, and the keyboard traversal that shows where the keyboard went.",
};

/// The thing can be acted on.
pub const INTERACTIVE: State = State {
    id: "interactive",
    role: None,
    treatment: "A hit region and a place in the focus order, so the thing is reachable without a pointer.",
    evidence: "A keyboard traversal, and a pointer capture of the same region.",
};

/// The thing holds something that is not acceptable.
pub const INVALID: State = State {
    id: "invalid",
    role: Some("critical"),
    treatment: "The critical treatment on the field, and the message that says why, in text.",
    evidence: "A capture of the invalid state, and a check that the message is there.",
};

/// The thing is switched on.
pub const ON: State = State {
    id: "on",
    role: Some("selection"),
    treatment: "The selection treatment on the surface and the edge, and a state a screen reader reads.",
    evidence: "The selected-state semantics, and a capture of both states.",
};
