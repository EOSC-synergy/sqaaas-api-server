(
{%- set im_server = template_kwargs.get("im_server") -%}
{%- set im_auth_file = "/im/auth.dat" -%}
{%- set openstack_site_id = template_kwargs.get("openstack_site_id") -%}
{%- set openstack_url = template_kwargs.get("openstack_url") -%}
{%- set openstack_port = template_kwargs.get("openstack_port") -%}
{%- set openstack_tenant_name = template_kwargs.get("openstack_tenant_name") -%}
{%- set openstack_domain_name = template_kwargs.get("openstack_domain_name") -%}
{%- set openstack_tenant_domain_id = template_kwargs.get("openstack_tenant_domain_id") -%}
{%- set openstack_auth_version = template_kwargs.get("openstack_auth_version") -%}
mkdir /im
cat <<EOF >> {{ im_auth_file }}
# InfrastructureManager auth
type = InfrastructureManager; username = %s; password = %s
# OpenStack site using standard user, password, tenant format
id = {{ openstack_site_id }}; type = OpenStack; host = {{ openstack_url }}:{{ openstack_port }}; username = %s; password = %s; tenant = {{ openstack_tenant_name }}; tenant_domain_id = {{ openstack_tenant_domain_id }}; domain = {{ openstack_domain_name }}; auth_version = {{ openstack_auth_version }}
EOF
if [ -z "$IM_USER" ] || [ -z "$IM_PASS" ] || [ -z "$OPENSTACK_USER" ] || [ -z "$OPENSTACK_PASS" ]; then
  echo 'One or more credential variables are undefined (required: IM_USER, IM_PASS, OPENSTACK_USER, OPENSTACK_PASS)'
  exit 1
fi
printf "$(cat {{ im_auth_file }})" "${IM_USER}" "${IM_PASS}" "${OPENSTACK_USER}" "${OPENSTACK_PASS}" > {{ im_auth_file }}
echo "Generated auth.dat file:"
ls -l {{ im_auth_file }}
echo

{% if template in ['im_client'] %}
{%- set im_config_file_name = template_kwargs.get("im_config_file", "") -%}
{%- set im_config_file = checkout_dir ~ "/" ~ im_config_file_name -%}
{% if checkout_dir not in ['.'] %}
cp {{ im_config_file_name }} {{ im_config_file }}
{% endif %}
{%- set im_config_file_type = template_kwargs.get("im_config_file_type", "") -%}
echo "Printing IM config file: {{ im_config_file }}"
cat {{ im_config_file }}
im_client.py -r "{{ im_server }}" -a "{{ im_auth_file }}" create_wait_outputs {{ im_config_file }} > ./im_{{ im_config_file_type }}.json
RETURN_CODE=$?
echo "im_client.py create_wait_outputs return code: ${RETURN_CODE}"
echo "Infrastructure Manager output:"
cat ./im_{{ im_config_file_type }}.json
awk "/\{/,/\}/ { print $1 }" ./im_{{ im_config_file_type }}.json > ./im_{{ im_config_file_type }}_aux.json
echo "Infrastructure Manager output (only json part):"
cat ./im_{{ im_config_file_type }}_aux.json
echo
INFID=$(jq -r '[ .infid ] | .[]' ./im_{{ im_config_file_type }}_aux.json)
echo "INFID=${INFID}"
if [ ${RETURN_CODE} -eq 0 ] && ! [[ -z "${INFID}" && "x${INFID}x" == "xnullx" ]]; then
  echo "Deployment finished with success. Logs:"
  im_client.py -r "{{ im_server }}" -a "{{ im_auth_file }}" getcontmsg ${INFID}
  echo
  im_client.py -r "{{ im_server }}" -a "{{ im_auth_file }}" destroy ${INFID}
  echo "im_client.py destroy return code: $?"
elif ! [[ -z "${INFID}" && "x${INFID}x" == "xnullx" ]]; then
  echo "Deployment failed. Logs:"
  im_client.py -r "{{ im_server }}" -a "{{ im_auth_file }}" getcontmsg ${INFID}
  echo
  im_client.py -r "{{ im_server }}" -a "{{ im_auth_file }}" destroy ${INFID}
  echo "im_client.py destroy return code: $?"
  exit ${RETURN_CODE}
else
  exit ${RETURN_CODE}
fi
{%- elif template in ['ec3_client'] %}
{%- set ec3_templates_path = "/etc/ec3/templates" -%}
{%- set ec3_templates = template_kwargs.get("ec3_templates") -%}
{%- set ec3_templates_local_dirs = template_kwargs.get("ec3_templates_local_dirs") -%}
mkdir -p {{ ec3_templates_path }}
{%- for _local_dir in ec3_templates_local_dirs %}
{%- if _local_dir not in ['.'] %}
{%- set _checkout_path = checkout_dir ~ "/" ~ _local_dirs -%}
{%- else %}
{%- set _checkout_path = checkout_dir -%}
{%- endif %}
cp -rf {{ _checkout_path }}/* {{ ec3_templates_path }}
{%- endfor %}
ec3 launch sqaaas_ec3_cluster {{ ec3_templates|join(' ') }} -a "{{ im_auth_file }}" -u {{ im_server }} -y
ec3 show sqaaas_ec3_cluster -r
ec3 destroy sqaaas_ec3_cluster --force -y
{%- endif %}
)
