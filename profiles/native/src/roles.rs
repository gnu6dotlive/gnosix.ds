//! Generated from core/ROLES.json. Do not edit.
//!
//! The semantic role layer as Rust constants: a role bound to a token on
//! the light substrate and on the dark one. A native target chooses a
//! substrate and reads the roles from it.

#![allow(dead_code)]

/// One substrate: every role, bound to a colour.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Substrate {
    pub surface: &'static str,
    pub surface_raised: &'static str,
    pub surface_overlay: &'static str,
    pub surface_sunken: &'static str,
    pub ink: &'static str,
    pub ink_muted: &'static str,
    pub hairline: &'static str,
    pub accent: &'static str,
    pub accent_ink: &'static str,
    pub focus: &'static str,
    pub selection: &'static str,
    pub info: &'static str,
    pub positive: &'static str,
    pub positive_surface: &'static str,
    pub caution: &'static str,
    pub critical: &'static str,
}

/// The light substrate.
pub const LIGHT: Substrate = Substrate {
    surface: crate::theme::colour::NEUTRAL_SHELL_WHITE,
    surface_raised: crate::theme::surface::SURFACE_LIGHT_L978C1,
    surface_overlay: crate::theme::surface::SURFACE_LIGHT_L988C0,
    surface_sunken: crate::theme::surface::SURFACE_LIGHT_L920C6,
    ink: crate::theme::colour::NEUTRAL_ANTHRACITE,
    ink_muted: crate::theme::surface::INK_ON_LIGHT_L445C22,
    hairline: crate::theme::surface::HAIRLINE_L921C5,
    accent: crate::theme::colour::SIGNAL_ORANGE_BASE,
    accent_ink: crate::theme::colour::NEUTRAL_ANTHRACITE,
    focus: crate::theme::colour::ROYAL_BLUE_BASE,
    selection: crate::theme::colour::ROYAL_BLUE_100,
    info: crate::theme::surface::INFO_L621C123,
    positive: crate::theme::colour::BERET_GREEN_BASE,
    positive_surface: crate::theme::colour::BERET_GREEN_100,
    caution: crate::theme::colour::SEMANTIC_WARN,
    critical: crate::theme::colour::SEMANTIC_ALERT,
};

/// The dark substrate.
pub const DARK: Substrate = Substrate {
    surface: crate::theme::colour::NEUTRAL_ANTHRACITE,
    surface_raised: crate::theme::surface::SURFACE_DARK_L250C14,
    surface_overlay: crate::theme::surface::SURFACE_DARK_L282C16,
    surface_sunken: crate::theme::surface::SURFACE_DARK_L207C10,
    ink: crate::theme::colour::NEUTRAL_SHELL_WHITE,
    ink_muted: crate::theme::surface::INK_ON_DARK_L678C24,
    hairline: crate::theme::surface::HAIRLINE_L310C15,
    accent: crate::theme::colour::SIGNAL_ORANGE_BASE,
    accent_ink: crate::theme::colour::NEUTRAL_ANTHRACITE,
    focus: crate::theme::colour::ROYAL_BLUE_BASE,
    selection: crate::theme::surface::SURFACE_SELECTION_L354C90,
    info: crate::theme::surface::INFO_L621C123,
    positive: crate::theme::colour::BERET_GREEN_300,
    positive_surface: crate::theme::colour::BERET_GREEN_700,
    caution: crate::theme::colour::SEMANTIC_WARN,
    critical: crate::theme::colour::SEMANTIC_ALERT,
};
