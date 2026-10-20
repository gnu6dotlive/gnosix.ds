package labs.gnuin.gnosixds

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun ReferenceScreen() {
    var requested by remember { mutableStateOf<String?>(null) }
    val observed: String? = null // Replace only after an actual result arrives.
    val state = projectState(requested, observed)
    Column(
        modifier = Modifier.fillMaxSize().background(GnosixColors.NeutralShellWhite)
            .verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp)
    ) {
        Text("gnos.ux", fontFamily = GnosixType.primary, fontWeight = FontWeight.Bold,
            fontSize = 32.sp, color = GnosixColors.NeutralAnthracite)
        Text("Three cube identities", fontFamily = GnosixType.primary,
            color = GnosixColors.NeutralAnthracite)
        Text(">_  right · orange", color = GnosixColors.SignalOrange700,
            modifier = Modifier.semantics { contentDescription = "Orange cube, right face, greater than underscore" })
        Text(">$  left · blue", color = GnosixColors.RoyalBlue700,
            modifier = Modifier.semantics { contentDescription = "Blue cube, left face, greater than dollar" })
        Text(">#  top · green", color = GnosixColors.BeretGreen700,
            modifier = Modifier.semantics { contentDescription = "Green cube, top face, greater than hash" })
        Button(
            onClick = { requested = "connected" },
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
            contentPadding = PaddingValues(16.dp),
            colors = ButtonDefaults.buttonColors(containerColor = GnosixColors.SignalOrangeBase)
        ) { Text("Request connection", color = GnosixColors.NeutralAnthracite) }
        Text(state.label,
            color = GnosixColors.NeutralAnthracite,
            modifier = Modifier.semantics { stateDescription = state.label })
    }
}
