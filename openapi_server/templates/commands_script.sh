(
cd {{ checkout_dir }} && 
    {%- for cmd in commands %}
    {{ cmd }}{{"&&" if not loop.last}}
    {%- endfor %}
)
