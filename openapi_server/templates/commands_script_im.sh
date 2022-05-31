(
{%- set im_config_file = template_kwargs.get("im_config_file", "") -%}
{%- if im_config_file.endswith("radl") %}
{%- set config_file_type = "radl" -%}
{%- else %}
{%- set config_file_type = "tosca" -%}
{%- endif %}
{%- set im_server = template_kwargs.get("im_server") -%}
{%- set openstack_site_id = template_kwargs.get("openstack_site_id") -%}
{%- set openstack_url = template_kwargs.get("openstack_url") -%}
{%- set openstack_port = template_kwargs.get("openstack_port") -%}
{%- set openstack_tenant_name = template_kwargs.get("openstack_tenant_name") -%}
{%- set openstack_domain_name = template_kwargs.get("openstack_domain_name") -%}
{%- set openstack_auth_version = template_kwargs.get("openstack_auth_version") -%}
{%- set im_auth_file = "/im/auth.dat" -%}
mkdir /im
cat <<EOF >> {{ im_auth_file }}
# InfrastructureManager auth
type = InfrastructureManager; username = %s; password = %s
# OpenStack site using standard user, password, tenant format
id = {{ openstack_site_id }}; type = OpenStack; host = {{ openstack_url }}:{{ openstack_port }}; username = %s; password = %s; tenant = {{ openstack_tenant_name }}; domain = {{ openstack_domain_name }}; auth_version = {{ openstack_auth_version }}
EOF
if [ -z "$IM_USER" ] || [ -z "$IM_PASS" ] || [ -z "$OPENSTACK_USER" ] || [ -z "$OPENSTACK_PASS" ]; then
  echo 'One or more credential variables are undefined (required: IM_USER, IM_PASS, OPENSTACK_USER, OPENSTACK_PASS)'
  exit 1
fi
printf "$(cat {{ im_auth_file }})" "${IM_USER}" "${IM_PASS}" "${OPENSTACK_USER}" "${OPENSTACK_PASS}" > {{ im_auth_file }}
echo "Generated auth.dat file:"
ls -l {{ im_auth_file }}
printf "$(cat {{im_config_file}})" "{{ openstack_url }}" "{{ radl_image_id }}" > /im/test-ost.{{ config_file_type }}
echo "Printing {{ config_file_type }} file"
cat /im/test-ost.{{ config_file_type }}
echo
im_client.py -r "{{ im_server }}" -a "{{ im_auth_file }}" create_wait_outputs /im/test-ost.{{ config_file_type }} > ./im_{{ config_file_type }}.json
RETURN_CODE=$?
echo "im_client.py create_wait_outputs return code: ${RETURN_CODE}"
echo "Infrastructure Manager output:"
cat ./im_{{ config_file_type }}.json
awk "/\{/,/\}/ { print $1 }" ./im_{{ config_file_type }}.json > ./im_{{ config_file_type }}_aux.json
echo "Infrastructure Manager output (only json part):"
cat ./im_{{ config_file_type }}_aux.json
echo
INFID=$(jq -r '[ .infid ] | .[]' ./im_{{ config_file_type }}_aux.json)
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
)
