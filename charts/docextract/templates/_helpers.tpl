{{- define "docextract.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "docextract.fullname" -}}
{{- default .Release.Name .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "docextract.labels" -}}
app.kubernetes.io/name: {{ include "docextract.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end -}}

{{- define "docextract.selectorLabels" -}}
app.kubernetes.io/name: {{ include "docextract.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
