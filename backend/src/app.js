const express = require('express');
const cors = require('cors');
require('dotenv').config({ path: require('path').resolve(__dirname, '../../../.env') });
const hotVideosRouter = require('./routes/hotVideos');
const proxyRouter = require('./routes/proxy');
const userTrackRouter = require('./routes/userTrack');
const upProfileRouter = require('./routes/upProfile') 
const llmConfigRouter = require('./routes/llmConfig');
// const upAnalysisRouter = require('./routes/upProfile/analysis')

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// 路由
app.use('/api/hot-videos', hotVideosRouter);
app.use('/api/user-track', userTrackRouter);
app.use('/proxy', proxyRouter);
app.use('/api/up-profile', upProfileRouter);
app.use('/api/llm-config', llmConfigRouter);
// app.use('/api/up-analysis', upAnalysisRouter);

// 404处理
app.use((req, res) => {
  res.status(404).json({ message: '接口不存在' });
});

app.listen(PORT, () => {
  console.log(`服务器已启动，端口：${PORT}`);
}); 
