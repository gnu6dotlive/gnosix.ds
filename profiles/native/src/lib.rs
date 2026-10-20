//! The gnosix portable contract, as Rust constants.
//!
//! This crate is the native projection of `core/TOKENS.json` and
//! `core/SURFACES.json`. The values are generated; see `src/theme.rs`. A
//! gnos.ux implementation consumes them and does not restate them, which is
//! the whole point of the projection boundary: the meaning is portable and
//! the rendering is not.
//!
//! What is *not* here is the GPUI adapter. The engine is pre-1.0 and its API
//! is version-scoped, so a binding to it would date the package; the
//! mapping in `../README.md` says what the adapter has to do.

pub mod roles;
pub mod theme;

#[cfg(test)]
mod tests {
    /// The palette is the approved one. A change to the token source is a
    /// change to this file, and the test is what says so.
    #[test]
    fn the_palette_is_the_approved_one() {
        assert_eq!(super::theme::colour::NEUTRAL_ANTHRACITE, "#111418");
        assert_eq!(super::theme::colour::NEUTRAL_SHELL_WHITE, "#F7F3ED");
        assert_eq!(super::theme::colour::SIGNAL_ORANGE_BASE, "#FF6A00");
        assert_eq!(super::theme::colour::ROYAL_BLUE_BASE, "#4169E1");
    }

    /// The measured contrast of each approved pairing.
    #[test]
    fn the_measured_pairings_are_the_approved_ones() {
        assert!(super::theme::contrast::ANTHRACITE_ON_SHELL_WHITE > 15.0);
        assert!(super::theme::contrast::PURE_WHITE_ON_SIGNAL_ORANGE < 3.0);
        assert!(super::theme::contrast::PURE_WHITE_ON_BERET_GREEN > 4.5);
    }

    /// The role layer is present, and it is bound to the system's own
    /// tokens on both substrates. A role layer that is not bound to a
    /// token is a second palette.
    #[test]
    fn the_role_layer_is_bound_to_the_contract() {
        assert_eq!(super::roles::LIGHT.surface, super::theme::colour::NEUTRAL_SHELL_WHITE);
        assert_eq!(super::roles::DARK.surface, super::theme::colour::NEUTRAL_ANTHRACITE);
        assert_eq!(super::roles::LIGHT.accent, super::theme::colour::SIGNAL_ORANGE_BASE);
        assert_eq!(super::roles::DARK.focus, super::theme::colour::ROYAL_BLUE_BASE);
        assert_eq!(super::roles::LIGHT.ink, super::theme::colour::NEUTRAL_ANTHRACITE);
        assert_eq!(super::roles::DARK.ink, super::theme::colour::NEUTRAL_SHELL_WHITE);
    }

    /// The surface layer is present, and it is the system's own.
    #[test]
    fn the_surface_layer_is_carried() {
        assert!(!super::theme::surface::SURFACE_DARK_L207C10.is_empty());
        assert!(super::theme::surface::SURFACE_LIGHT_L952C7.len() == 7);
    }
}
