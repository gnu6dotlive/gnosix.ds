package labs.gnuin.gnosixds

import androidx.compose.runtime.Composable
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily

// V3.2 packages the same Space Grotesk variable family for native targets.
// The profile remains `mapped` until an actual Compose render is captured and checked.
object GnosixType {
    val primary = FontFamily(Font(R.font.space_grotesk))
    val technical = primary
}

@Composable
fun GnosixTheme(content: @Composable () -> Unit) = content()
