{{/*
Expand the name of the chart.
*/}}
{{- define "userservice.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "userservice.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "userservice.opaFullname" -}}
{{- printf "%s-opa" .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "userservice.mongoFullname" -}}
{{- printf "%s-mongo" .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "userservice.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}

{{- define "userservice.commonLabels" -}}
helm.sh/chart: {{ include "userservice.chart" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "userservice.labels" -}}
{{ include "userservice.selectorLabels" . }}
{{ include "userservice.commonLabels" . }}
{{- end }}

{{- define "userservice.opaLabels" -}}
{{ include "userservice.opaSelectorLabels" . }}
{{ include "userservice.commonLabels" . }}
{{- end }}

{{- define "userservice.mongoLabels" -}}
{{ include "userservice.mongoSelectorLabels" . }}
{{ include "userservice.commonLabels" . }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "userservice.selectorLabels" -}}
app.kubernetes.io/name: {{ include "userservice.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: userservice
{{- end }}

{{- define "userservice.opaSelectorLabels" -}}
app.kubernetes.io/name: opa
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: opa
{{- end }}


{{- define "userservice.mongoSelectorLabels" -}}
app.kubernetes.io/name: mongo
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: mongo
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "userservice.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "userservice.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
