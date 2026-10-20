//! Generated from core/TOKENS.json and core/SURFACES.json. Do not edit.
//!
//! The gnosix portable contract as Rust constants: the palette, the
//! surfaces, the measured contrast ratios, the spacing and the weights.
//! A target implementation consumes these; it does not restate them.

#![allow(dead_code)]

/// The approved palette.
pub mod colour {
    pub const NEUTRAL_ANTHRACITE: &str = "#111418";
    pub const NEUTRAL_SHELL_WHITE: &str = "#F7F3ED";
    pub const NEUTRAL_PURE_WHITE: &str = "#FFFFFF";
    pub const NEUTRAL_HAIRLINE: &str = "#D7DADF";
    pub const NEUTRAL_QUIET_DIVIDER: &str = "#E6E8EB";
    pub const NEUTRAL_MUTED: &str = "#A1A6AD";
    pub const NEUTRAL_SLATE: &str = "#667085";
    pub const SIGNAL_ORANGE_100: &str = "#FFE5D2";
    pub const SIGNAL_ORANGE_300: &str = "#FF8E40";
    pub const SIGNAL_ORANGE_BASE: &str = "#FF6A00";
    pub const SIGNAL_ORANGE_700: &str = "#C95400";
    pub const BERET_GREEN_100: &str = "#E8EFE5";
    pub const BERET_GREEN_300: &str = "#8DA982";
    pub const BERET_GREEN_BASE: &str = "#5F7F52";
    pub const BERET_GREEN_700: &str = "#455F3D";
    pub const ROYAL_BLUE_100: &str = "#E8EDFF";
    pub const ROYAL_BLUE_300: &str = "#87A0F4";
    pub const ROYAL_BLUE_BASE: &str = "#4169E1";
    pub const ROYAL_BLUE_700: &str = "#2446A8";
    pub const SEMANTIC_ALERT: &str = "#E5484D";
    pub const SEMANTIC_WARN: &str = "#F5A524";
}

/// The surface layer.
pub mod surface {
    pub const SURFACE_DARK_L166C12: &str = "#0B0F14";
    pub const SURFACE_DARK_L207C10: &str = "#14181C";
    pub const SURFACE_DARK_L211C10: &str = "#15191D";
    pub const SURFACE_DARK_L216C12: &str = "#161A1F";
    pub const SURFACE_DARK_L220C12: &str = "#171B20";
    pub const SURFACE_DARK_L236C12: &str = "#1A1F24";
    pub const SURFACE_DARK_L250C14: &str = "#1D2228";
    pub const SURFACE_DARK_L262C12: &str = "#20252A";
    pub const SURFACE_DARK_L262C13: &str = "#20252B";
    pub const SURFACE_DARK_L282C16: &str = "#242A31";
    pub const SURFACE_DARK_L285C15: &str = "#242B31";
    pub const SURFACE_DARK_L343C15: &str = "#323A40";
    pub const SURFACE_DARK_L348C16: &str = "#343B42";
    pub const SURFACE_DARK_L372C19: &str = "#39414A";
    pub const SURFACE_DARK_L486C23: &str = "#55616C";
    pub const SURFACE_DARK_L505C22: &str = "#5B6671";
    pub const SURFACE_LIGHT_L700C24: &str = "#93A0AD";
    pub const SURFACE_LIGHT_L886C7: &str = "#D6DADE";
    pub const SURFACE_LIGHT_L908C6: &str = "#DDE1E4";
    pub const SURFACE_LIGHT_L920C6: &str = "#E1E5E8";
    pub const SURFACE_LIGHT_L933C4: &str = "#E9E9E6";
    pub const SURFACE_LIGHT_L952C7: &str = "#F1EFEA";
    pub const SURFACE_LIGHT_L953C2: &str = "#EEF0EF";
    pub const SURFACE_LIGHT_L966C2: &str = "#F2F4F5";
    pub const SURFACE_LIGHT_L969C2: &str = "#F3F5F6";
    pub const SURFACE_LIGHT_L978C1: &str = "#F7F8F8";
    pub const SURFACE_LIGHT_L988C0: &str = "#FBFBFB";
    pub const INK_ON_DARK_L678C24: &str = "#8D99A6";
    pub const INK_ON_DARK_L766C20: &str = "#AAB4C0";
    pub const INK_ON_DARK_L775C18: &str = "#ADB7C1";
    pub const INK_ON_DARK_L775C16: &str = "#AEB7C0";
    pub const INK_ON_DARK_L836C12: &str = "#C3CAD1";
    pub const INK_ON_DARK_L840C10: &str = "#C6CBD1";
    pub const INK_ON_DARK_L858C12: &str = "#CBD1D8";
    pub const INK_ON_DARK_L873C10: &str = "#D0D6DC";
    pub const INK_ON_DARK_L883C10: &str = "#D4D9DF";
    pub const INK_ON_DARK_L884C8: &str = "#D5D9DE";
    pub const INK_ON_LIGHT_L342C06: &str = "#37393C";
    pub const INK_ON_LIGHT_L445C22: &str = "#4B5560";
    pub const INK_ON_LIGHT_L454C24: &str = "#4C5863";
    pub const INK_ON_LIGHT_L461C23: &str = "#4E5A65";
    pub const INK_ON_LIGHT_L468C23: &str = "#505C67";
    pub const INK_ON_LIGHT_L481C25: &str = "#52606B";
    pub const INK_ON_LIGHT_L487C21: &str = "#56616B";
    pub const INK_ON_LIGHT_L495C20: &str = "#59636D";
    pub const INK_ON_LIGHT_L499C23: &str = "#5A6470";
    pub const INK_ON_LIGHT_L509C20: &str = "#5D6771";
    pub const INK_ON_LIGHT_L539C22: &str = "#64707B";
    pub const INK_ON_LIGHT_L546C22: &str = "#66727D";
    pub const INK_ON_LIGHT_L554C23: &str = "#697480";
    pub const HAIRLINE_L310C15: &str = "#2B3138";
    pub const HAIRLINE_L345C13: &str = "#343A40";
    pub const HAIRLINE_L353C15: &str = "#363C43";
    pub const HAIRLINE_L405C17: &str = "#424A52";
    pub const HAIRLINE_L431C20: &str = "#48515B";
    pub const HAIRLINE_L489C18: &str = "#59616A";
    pub const HAIRLINE_L705C17: &str = "#98A1AA";
    pub const HAIRLINE_L714C14: &str = "#9CA4AB";
    pub const HAIRLINE_L785C7: &str = "#B6B9BD";
    pub const HAIRLINE_L804C10: &str = "#B9C0C5";
    pub const HAIRLINE_L858C6: &str = "#CDD1D4";
    pub const HAIRLINE_L865C6: &str = "#CFD3D6";
    pub const HAIRLINE_L871C7: &str = "#D1D5D9";
    pub const HAIRLINE_L907C7: &str = "#DCE1E4";
    pub const HAIRLINE_L917C4: &str = "#E1E4E6";
    pub const HAIRLINE_L921C5: &str = "#E3E5E8";
    pub const HAIRLINE_L926C4: &str = "#E4E7E9";
    pub const INK_POSITIVE_L377C22: &str = "#39453C";
    pub const SURFACE_POSITIVE_L909C18: &str = "#DCE4D8";
    pub const SURFACE_WARM_L971C18: &str = "#FFF3EA";
    pub const SURFACE_SELECTION_L354C90: &str = "#25396B";
}

/// The measured contrast of each approved pairing.
pub mod contrast {
    pub const ANTHRACITE_ON_SHELL_WHITE: f64 = 16.71;
    pub const SHELL_WHITE_ON_ANTHRACITE: f64 = 16.71;
    pub const ANTHRACITE_ON_SIGNAL_ORANGE: f64 = 6.43;
    pub const PURE_WHITE_ON_SIGNAL_ORANGE: f64 = 2.87;
    pub const PURE_WHITE_ON_BERET_GREEN: f64 = 4.52;
    pub const PURE_WHITE_ON_ROYAL_BLUE: f64 = 4.85;
    pub const SHELL_WHITE_ON_ROYAL_BLUE: f64 = 4.38;
}

/// The ratified spacing steps.
pub mod spacing {
    pub const S_2XS: f64 = 4.0;
    pub const XS: f64 = 8.0;
    pub const SM: f64 = 12.0;
    pub const MD: f64 = 16.0;
    pub const LG: f64 = 24.0;
    pub const XL: f64 = 32.0;
    pub const S_2XL: f64 = 48.0;
    pub const S_3XL: f64 = 64.0;
    pub const S_4XL: f64 = 96.0;
    pub const S_5XL: f64 = 128.0;
}

/// The ratified weights.
pub mod weight {
    pub const REGULAR: u16 = 400;
    pub const MEDIUM: u16 = 500;
    pub const SEMIBOLD: u16 = 600;
    pub const BOLD: u16 = 700;
}
