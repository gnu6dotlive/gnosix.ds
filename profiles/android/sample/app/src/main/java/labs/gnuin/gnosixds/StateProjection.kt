package labs.gnuin.gnosixds

data class ProjectedState(val label: String, val pending: Boolean)

fun projectState(requested: String?, observed: String?): ProjectedState =
    if (requested != null && requested != observed) ProjectedState("Request pending", true)
    else ProjectedState("Observed: ${observed ?: "unchanged"}", false)
