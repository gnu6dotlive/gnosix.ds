//! The example in README.md, compiled so that the README cannot drift
//! away from the crate without the suite noticing.

#[test]
fn the_readme_example_works() {
    let theme = gnosix_ds::roles::DARK;
    let surface = theme.surface;
    assert_eq!(surface, "#111418");
}
