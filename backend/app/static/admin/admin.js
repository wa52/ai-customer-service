const $ = (id) => document.getElementById(id);
const form = $('config-form');
const temp = $('llm_temperature');
const notice = $('notice');

function render(data) {
  $('llm_provider').value = data.llm_provider || 'openai_compatible';
  $('llm_base_url').value = data.llm_base_url || '';
  $('llm_model').value = data.llm_model || '';
  temp.value = data.llm_temperature ?? 0.3;
  $('temperature-value').value = temp.value;
  $('product_capability_enabled').checked = Boolean(data.product_capability_enabled);
  $('status-title').textContent = data.configured ? '模型已连接' : '等待配置模型';
  $('status-subtitle').textContent = data.configured ? `${data.llm_provider} · 可开始对话` : '填写云端模型信息后即可使用';
  $('fact-model').textContent = data.llm_model || '未设置';
  $('fact-key').textContent = data.api_key_set ? (data.api_key_masked || '已设置') : '未设置';
  $('fact-memory').textContent = data.memory_provider || 'memory';
  $('status-dot').style.background = data.configured ? '#59ca99' : '#efb45f';
}

temp.addEventListener('input', () => { $('temperature-value').value = temp.value; });
$('toggle-key').addEventListener('click', () => {
  const input = $('llm_api_key');
  input.type = input.type === 'password' ? 'text' : 'password';
  $('toggle-key').textContent = input.type === 'password' ? '显示' : '隐藏';
});

async function load() {
  const response = await fetch('/api/v1/admin/config');
  render(await response.json());
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  notice.textContent = '正在保存…';
  const response = await fetch('/api/v1/admin/config', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({
    llm_provider: $('llm_provider').value, llm_base_url: $('llm_base_url').value.trim(), llm_model: $('llm_model').value.trim(),
    llm_api_key: $('llm_api_key').value, llm_temperature: Number(temp.value), product_capability_enabled: $('product_capability_enabled').checked
  })});
  if (!response.ok) { notice.textContent = '保存失败，请检查输入'; notice.style.color = '#c45d4b'; return; }
  render(await response.json()); $('llm_api_key').value = ''; notice.textContent = '已保存，下一条消息立即使用新配置'; notice.style.color = '#3b9773';
});

load().catch(() => { notice.textContent = '无法读取后端配置'; notice.style.color = '#c45d4b'; });
