const $ = (id) => document.getElementById(id);
const form = $('config-form');
const temp = $('llm_temperature');
const notice = $('notice');
const providers = [
  ['deepseek', 'DeepSeek', 'V4.1 Flash', 'https://api.deepseek.com', ['deepseek-flash', 'deepseek-v4-pro']],
  ['openai', 'OpenAI', 'GPT 系列', 'https://api.openai.com/v1', ['gpt-5.6-luna', 'gpt-5.6-terra', 'gpt-5.6-sol', 'gpt-5.5', 'gpt-4.1-mini']],
  ['anthropic', 'Anthropic', 'Claude 系列', 'https://api.anthropic.com/v1', ['claude-sonnet-4-6', 'claude-opus-4-8', 'claude-haiku-4-5-20251001']],
  ['gemini', 'Google Gemini', 'Gemini 系列', 'https://generativelanguage.googleapis.com/v1beta/openai', ['gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.6-flash', 'gemini-3.1-pro-preview']],
  ['qwen', '通义千问', 'Qwen 系列', 'https://dashscope.aliyuncs.com/compatible-mode/v1', ['qwen3.8-max', 'qwen3.8-flash', 'qwen3.7-plus', 'qwen3.7-flash', 'qwen3-coder-plus']],
  ['zhipu', '智谱 GLM', 'GLM 系列', 'https://open.bigmodel.cn/api/paas/v4', ['glm-5-turbo', 'glm-5', 'glm-4.7', 'glm-4.6']],
  ['moonshot', '月之暗面', 'Kimi 系列', 'https://api.moonshot.cn/v1', ['kimi-k2.6', 'kimi-k2.5', 'kimi-k3', 'kimi-k2.7-code']],
  ['minimax', 'MiniMax', 'M 系列', 'https://api.minimax.chat/v1', ['MiniMax-M3', 'MiniMax-M2.7', 'MiniMax-M2.5']],
  ['openai_compatible', '自定义接口', 'OpenAI 兼容', '', []],
];
const picker = $('provider-picker');
providers.forEach(([value, name, desc]) => {
  const button = document.createElement('button');
  button.type = 'button'; button.className = 'provider-option'; button.dataset.provider = value;
  button.innerHTML = `<b>${name.slice(0, 2)}</b><span>${name}<small>${desc}</small></span>`;
  button.addEventListener('click', () => selectProvider(value, button));
  picker.appendChild(button);
});
function updateModels(models, current = '') {
  const select = $('llm_model');
  select.innerHTML = '';
  models.forEach((model) => select.add(new Option(model, model)));
  if (current && !models.includes(current)) select.add(new Option(`${current}（当前配置）`, current));
  if (current) select.value = current;
}
function selectProvider(value, button, current = '') {
  const preset = providers.find((item) => item[0] === value);
  $('llm_provider').value = value;
  document.querySelectorAll('.provider-option').forEach((item) => item.classList.toggle('active', item === button));
  if (preset) {
    $('llm_base_url').value = preset[3];
    $('llm_base_url').readOnly = value !== 'openai_compatible';
    $('llm_base_url').classList.toggle('official-url', value !== 'openai_compatible');
    updateModels(preset[4], current || preset[4][0] || '');
  }
}

function render(data) {
  $('llm_provider').value = data.llm_provider || 'openai_compatible';
  $('llm_base_url').value = data.llm_base_url || '';
  $('llm_base_url').readOnly = data.llm_provider !== 'openai_compatible';
  $('llm_base_url').classList.toggle('official-url', data.llm_provider !== 'openai_compatible');
  const provider = providers.find((item) => item[0] === data.llm_provider) || providers.at(-1);
  updateModels(provider[4], data.llm_model || '');
  temp.value = data.llm_temperature ?? 0.3;
  $('temperature-value').value = temp.value;
  $('product_capability_enabled').checked = Boolean(data.product_capability_enabled);
  document.querySelectorAll('.provider-option').forEach((item) => item.classList.toggle('active', item.dataset.provider === data.llm_provider));
  $('status-title').textContent = data.configured ? '模型已连接' : '等待连接';
  $('status-subtitle').textContent = data.configured ? `${data.llm_provider} · 可开始对话` : '填写云端模型信息后即可使用';
  $('fact-provider').textContent = data.llm_provider || '—';
  $('fact-model').textContent = data.llm_model || '未设置';
  $('fact-key').textContent = data.api_key_set ? (data.api_key_masked || '已设置') : '未设置';
  $('connection-badge').textContent = data.configured ? '已连接' : '未连接';
  $('connection-badge').classList.toggle('connected', data.configured);
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
    llm_provider: $('llm_provider').value, llm_base_url: $('llm_base_url').value.trim(), llm_model: $('llm_model').value,
    llm_api_key: $('llm_api_key').value, llm_temperature: Number(temp.value), product_capability_enabled: $('product_capability_enabled').checked
  })});
  if (!response.ok) { notice.textContent = '保存失败，请检查输入'; notice.style.color = '#c45d4b'; return; }
  render(await response.json()); $('llm_api_key').value = ''; notice.textContent = '已保存，下一条消息立即使用新配置'; notice.style.color = '#3b9773';
});

load().catch(() => { notice.textContent = '无法读取后端配置'; notice.style.color = '#c45d4b'; });
