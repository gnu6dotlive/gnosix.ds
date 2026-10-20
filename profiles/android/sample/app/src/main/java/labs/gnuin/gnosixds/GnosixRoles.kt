// Generated from core/ROLES.json. Do not edit.
//
// The semantic role layer as Compose colours: a role bound to a token on
// the light substrate and on the dark one.

package labs.gnuin.gnosixds

import androidx.compose.ui.graphics.Color

object GnosixRoles {
    /** The light substrate. */
    val Light: Map<String, Color> = mapOf(
        "surface" to Color(0xFFF7F3ED),
        "surface-raised" to Color(0xFFF7F8F8),
        "surface-overlay" to Color(0xFFFBFBFB),
        "surface-sunken" to Color(0xFFE1E5E8),
        "ink" to Color(0xFF111418),
        "ink-muted" to Color(0xFF4B5560),
        "hairline" to Color(0xFFE3E5E8),
        "accent" to Color(0xFFFF6A00),
        "accent-ink" to Color(0xFF111418),
        "focus" to Color(0xFF4169E1),
        "selection" to Color(0xFFE8EDFF),
        "info" to Color(0xFF3D8DCC),
        "positive" to Color(0xFF5F7F52),
        "positive-surface" to Color(0xFFE8EFE5),
        "caution" to Color(0xFFF5A524),
        "critical" to Color(0xFFE5484D),
    )

    /** The dark substrate. */
    val Dark: Map<String, Color> = mapOf(
        "surface" to Color(0xFF111418),
        "surface-raised" to Color(0xFF1D2228),
        "surface-overlay" to Color(0xFF242A31),
        "surface-sunken" to Color(0xFF14181C),
        "ink" to Color(0xFFF7F3ED),
        "ink-muted" to Color(0xFF8D99A6),
        "hairline" to Color(0xFF2B3138),
        "accent" to Color(0xFFFF6A00),
        "accent-ink" to Color(0xFF111418),
        "focus" to Color(0xFF4169E1),
        "selection" to Color(0xFF25396B),
        "info" to Color(0xFF3D8DCC),
        "positive" to Color(0xFF8DA982),
        "positive-surface" to Color(0xFF455F3D),
        "caution" to Color(0xFFF5A524),
        "critical" to Color(0xFFE5484D),
    )

    /** The role, in the substrate the theme is in. */
    fun of(substrate: String, role: String): Color =
        (if (substrate == "dark") Dark else Light)[role]
        ?: error("the contract has no role named $role")
}
