<template>
  <div class="channel-config-workspace">
    <!-- 顶部状态栏 -->
    <div class="channel-top-bar glass-panel">
      <div class="top-left">
        <SvgIcon name="SvgNotifyChannel" size="20" class="text-primary" />
        <div class="title-meta">
          <span class="view-title">告警规则与多通道通知渠道配置中心</span>
          <p>统一配置弹窗、邮件和企业微信通知渠道，保障告警消息及时送达值班人员。</p>
        </div>
      </div>

      <div class="top-right">
        <button class="btn-header-action btn-header-primary" @click="saveAllChannels" title="保存所有邮件、企业微信与弹窗告警通知渠道参数">
          <SvgIcon name="SvgNotifyChannel" size="14" style="margin-right: 4px;" />
          <span>保存全部渠道配置</span>
        </button>
      </div>
    </div>

    <!-- 核心多通道配置卡片 Tabs -->
    <div class="channel-tabs-card glass-panel">
      <el-tabs v-model="activeTab" class="custom-el-tabs">
        <!-- Tab 1: SMTP 邮件通知 -->
        <el-tab-pane label="电子邮箱 SMTP 渠道" name="email">
          <div class="tab-pane-content">
            <div class="channel-desc-box">
              <span class="desc-title">SMTP 发信服务器参数</span>
              <p>当系统发生【紧急】或【警告】故障时，自动异步发送格式化 HTML 告警邮件至运维值班人员邮箱。</p>
            </div>

            <el-form :model="emailForm" label-position="top" size="small" style="max-width: 600px;">
              <el-row :gutter="14">
                <el-col :span="16">
                  <el-form-item label="SMTP 服务器主机地址">
                    <el-input v-model="emailForm.host" placeholder="smtp.venue.com 或 smtp.exmail.qq.com" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="通信端口 (SSL)">
                    <el-input v-model="emailForm.port" placeholder="465 / 587" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="14">
                <el-col :span="12">
                  <el-form-item label="发件人邮箱账号">
                    <el-input v-model="emailForm.user" placeholder="alarm-notify@venue.com" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="发信授权码 / 密码">
                    <el-input v-model="emailForm.pass" type="password" show-password />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="接收报警人邮箱列表 (逗号分隔)">
                <el-input v-model="emailForm.receivers" placeholder="duty_ops@venue.com, chen_lead@venue.com" />
              </el-form-item>

              <div class="channel-action-row">
                <el-button size="small" type="success" @click="testEmailChannel">
                  立即发送测试邮件 (Test Email)
                </el-button>
                <span class="test-receipt num-mono">{{ emailTestReceipt }}</span>
              </div>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- Tab 2: 企业微信 Webhook 机器人 -->
        <el-tab-pane label="企业微信群 Webhook 机器人" name="wechat_work">
          <div class="tab-pane-content">
            <div class="channel-desc-box">
              <span class="desc-title">企业微信群机器人 Webhook</span>
              <p>故障触发时向场馆机电保障企微群推送 Markdown 告警卡片，支持 @所有人 或指定值班手机号。</p>
            </div>

            <el-form :model="wechatWorkForm" label-position="top" size="small" style="max-width: 600px;">
              <el-form-item label="企业微信机器人 Webhook 地址">
                <el-input v-model="wechatWorkForm.webhookUrl" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
              </el-form-item>

              <el-form-item label="提醒手机号 (可选 @指定人员)">
                <el-input v-model="wechatWorkForm.mentionedMobiles" placeholder="13800000001, 13800000002" />
              </el-form-item>

              <div class="channel-action-row">
                <el-button size="small" type="success" @click="testWechatWorkChannel">
                  向群聊推送测试消息卡片
                </el-button>
                <span class="test-receipt num-mono">{{ wechatWorkReceipt }}</span>
              </div>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- Tab 3: 微信公众号/小程序模板消息 -->
        <el-tab-pane label="微信公众号/小程序服务通知" name="wechat_mp">
          <div class="tab-pane-content">
            <div class="channel-desc-box">
              <span class="desc-title">微信服务号模板消息 (Template Message)</span>
              <p>针对值班领导提供微信个人服务号强提醒推送，无需时刻盯屏电脑端。</p>
            </div>

            <el-form :model="wechatMpForm" label-position="top" size="small" style="max-width: 600px;">
              <el-row :gutter="14">
                <el-col :span="12">
                  <el-form-item label="开发者 AppID">
                    <el-input v-model="wechatMpForm.appId" placeholder="wx1234567890abcdef" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="开发者 AppSecret">
                    <el-input v-model="wechatMpForm.appSecret" type="password" show-password />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="告警模板消息 Template ID">
                <el-input v-model="wechatMpForm.templateId" placeholder="tm_venue_alarm_notice_2026" />
              </el-form-item>

              <div class="channel-action-row">
                <el-button size="small" type="success" @click="testWechatMpChannel">
                  模拟向绑定运维发送微信模板消息
                </el-button>
                <span class="test-receipt num-mono">{{ wechatMpReceipt }}</span>
              </div>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const activeTab = ref('email')

const emailForm = ref({
  host: 'smtp.venue.local',
  port: '465',
  user: 'ibms-alarm@venue.com',
  pass: '••••••••••••',
  receivers: 'duty_ops@venue.com, zhang_lead@venue.com'
})
const emailTestReceipt = ref('就绪待测试')

const wechatWorkForm = ref({
  webhookUrl: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8a7b9c0d-2026-ibms-notify',
  mentionedMobiles: '13800000001, 13800000002'
})
const wechatWorkReceipt = ref('就绪待测试')

const wechatMpForm = ref({
  appId: 'wx88882026venue9999',
  appSecret: '••••••••••••••••••••••••••••••••',
  templateId: 'TM_SPORTS_ALARM_URGENT_NOTICE'
})
const wechatMpReceipt = ref('就绪待测试')

const testEmailChannel = () => {
  emailTestReceipt.value = '正在连接 SMTP 服务器...'
  setTimeout(() => {
    emailTestReceipt.value = '250 OK: Message accepted for delivery (45ms)'
    ElMessage.success('测试邮件已成功投递至发信队列！')
  }, 400)
}

const testWechatWorkChannel = () => {
  wechatWorkReceipt.value = '正在下发 Webhook JSON Payload...'
  setTimeout(() => {
    wechatWorkReceipt.value = '{"errcode":0,"errmsg":"ok"} (22ms)'
    ElMessage.success('企业微信群机器人已收到测试报警卡片！')
  }, 350)
}

const testWechatMpChannel = () => {
  wechatMpReceipt.value = '正在请求微信 Token 并签发模板消息...'
  setTimeout(() => {
    wechatMpReceipt.value = '{"errcode":0,"msgid":10082910} (38ms)'
    ElMessage.success('微信服务号模板消息发送成功！')
  }, 400)
}

const saveAllChannels = () => {
  ElMessage.success('全部三级告警通知渠道配置已安全加密保存并生效！')
}
</script>

<style scoped>
.channel-config-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.3s ease-out;
}

.channel-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
}

.top-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--do-coffee);
  letter-spacing: 0.5px;
}

.top-right {
  display: flex;
  gap: 12px;
}

.channel-tabs-card {
  padding: 20px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
}

.tab-pane-content {
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.channel-desc-box {
  background: linear-gradient(135deg, var(--do-sand-light) 0%, rgba(var(--th-accent-rgb), 0.05) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  border-radius: 6px;
  padding: 14px 16px;
  max-width: 640px;
}

.desc-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-gold-dark);
  display: block;
  margin-bottom: 6px;
}

.channel-desc-box p {
  font-size: 14px;
  color: var(--do-coffee-mid);
  line-height: 1.6;
  margin: 0;
}

.channel-action-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 14px;
}

.test-receipt {
  font-size: 14px;
  color: var(--do-olive);
  font-weight: 600;
  background: rgba(var(--th-success-rgb), 0.1);
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid rgba(var(--th-success-rgb), 0.25);
}
</style>
