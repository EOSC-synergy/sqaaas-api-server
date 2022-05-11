(
{%- if template %}
{%- if template.startswith("kubectl") %}
{%- if template in ["kubectl_config_files"] %}
{%- set k8s_config_files = template_kwargs.get("k8s_config_files", []) -%}
{%- set k8s_rollout_status_timeout = template_kwargs.get("k8s_rollout_status_timeout", "0") -%}
cat <<EOF >> {{ checkout_dir }}/kustomization.yaml
resources:
{%- for cfile in k8s_config_files %}
- {{ checkout_dir }}/{{ cfile }}
{%- endfor %}
EOF
{%- endif %}
kubectl apply -k {{ checkout_dir }}
if ! kubectl rollout status -k {{ checkout_dir }} --timeout={{ k8s_rollout_status_timeout }}; then
    kubectl rollout undo -k {{ checkout_dir }} --timeout={{ k8s_rollout_status_timeout }}
    kubectl rollout status -k {{ checkout_dir }} --timeout={{ k8s_rollout_status_timeout }}
fi
{% endif %}
{%- else %}
cd {{ checkout_dir }} &&
    {%- for cmd in commands %}
    {{ cmd }}{{"&&" if not loop.last}}
    {%- endfor %}
{% endif %}
{% endif %}
)
