# ✨ Parallax Pal - Your AI Research Companion

> 🚀 Supercharge your research with AI-powered analytics and insights

## 🌟 What is Parallax Pal?

Parallax Pal is your intelligent research assistant that transforms complex data into actionable insights. Whether you're a business analyst, researcher, or decision-maker, our platform harnesses the power of AI to deliver comprehensive research results in minutes, not hours.

## 🛠️ Project Status: 70-75% Complete

Parallax Pal is actively under development with core functionality in place. Major components implemented include:

- ✅ WebSocket-based real-time communication system
- ✅ JWT authentication with refresh tokens and API key support
- ✅ Multi-model AI orchestration framework
- ✅ Subscription management with tiered feature access
- ✅ Enhanced research pipeline with web scraping and analysis
- ✅ Terminal-inspired interface for technical users
- ✅ Backend infrastructure with FastAPI and SQLAlchemy
- ✅ React frontend with TypeScript and modern component architecture

##  Why Choose Parallax Pal?

### 🧠 Smart Research
- **Intelligent Analysis** - Multi-model AI processing for deeper insights
- **Real-time Updates** - Watch your research unfold live
- **Custom Workflows** - Tailor the research process to your needs
- **Lightning Fast** - Get results in minutes with GPU acceleration

### 🛡️ Enterprise Ready
- **Bank-Level Security** - Your data is protected with enterprise-grade encryption
- **Easy Integration** - Seamless API access for your existing tools
- **Smart Caching** - Lightning-fast response times
- **24/7 Monitoring** - Real-time system health checks

### 🎯 Perfect For...
📊 Market Research
📈 Competitive Analysis
📚 Academic Research
🔍 Data Mining
📑 Document Analysis
🌐 Web Intelligence


## 💎 Plans That Fit Your Needs

### Pay-As-You-Go
Perfect for occasional research needs:
- 🎯 Single Query: $7.99
- 🎯 5-Query Pack: $32.99 ($6.60/query)
- 🎯 10-Query Pack: $54.99 ($5.50/query)

or...

### Monthly Subscriptions
Choose the plan below that works for you!


## Key Features

### 🤖 AI Model Integration
- Multiple AI models working in harmony
- Model-specific strengths for different tasks
- Seamless switching between models

### 🖥️ Terminal Experience
- Familiar command-line interface
- Custom commands and shortcuts
- Real-time updates and progress tracking

### 🚄 Performance
- Optional/upgraded performance via GPU acceleration (supports NVIDIA, Apple Metal)
- Parallel processing capabilities
- Efficient resource management

### 🔒 Security
- End-to-end encryption
- Secure OAuth2 authentication
- Data privacy controls

## 🌈 Premium Features

### 💫 Advanced Capabilities
- GPU-accelerated processing
- Priority query handling
- Extended API access
- Custom model configuration
- Optional/upgraded local model integration via Ollama

### 📊 Enhanced Analytics
- Detailed research metrics
- Advanced visualization tools
- Export capabilities
- Custom reporting


## 💎 Pricing

Choose the plan that fits your needs:


#### 🆓 Free Tier
- Basic research capabilities
- 10 queries per month
- Community support
- Ad-supported
- $0/month

#### ⭐ Basic
- Ad-free experience
- Email support
- Basic analytics
- 50 queries per month
- Up to 5 continuous research tasks per month
- $35.99/month or $359.90/year (save 17%)

#### 🌟 Pro
- Advanced research features
- GPU acceleration for faster results
- Priority support
- 500 queries per month
- Up to 20 continuous research tasks per month
- Advanced visualization tools
- $95.99/month or $959.90/year (save 17%)

#### 🔮 Enterprise
- All Pro features
- Dedicated support team
- API access with custom rate limits
- Custom analytics dashboard
- Team collaboration features
- Contact sales for pricing

### ⚡ Privacy Plan - $1,499 one-time purchase
- All Pro features
- Local model configuration via Ollama
- Unlimited continuous research
- Full data sovereignty
- 6 months of Pro subscription included
- Annual renewal: $599


*All annual subscriptions get 2 months free!*

## 🚀 Get Started in Seconds

1. 📝 Sign up at [parallaxanalytics.com](https://parallaxanalytics.com)
2. 💳 Choose your plan
3. ✨ Start researching!

## 🔒 Your Data, Your Privacy

- Enterprise-grade security
- Data encryption at rest and in transit
- EU USERS: WHILE DATA IS ANONYMIZED/TELEMETRIZED, I CANNOT GUARANTEE COMPLIANCE WITH GDPR
- Regular security audits
- Clear, easy opt-outs
- Innovative, modularized data collection for academic/scientific purposes

### 💰 Data Sharing Discount Program

Share your research data and receive substantial subscription discounts. You control what you share:

| Sharing Tier | Discount | Example Data Types |
|--------------|----------|-------------------|
| **Basic** | 10% | • Anonymous query statistics<br>• General topic categories<br>• Usage patterns |
| **Standard** | 20% | • Anonymized search queries<br>• Result interaction metrics<br>• Feature utilization data |
| **Enhanced** | 30% | • Domain-specific research patterns<br>• Content categorization data<br>• Source preference information |
| **Premium** | 40% | • Full research corpus (anonymized)<br>• Custom workflow templates<br>• Industry-specific analysis patterns |

**Important Notes:**
- All shared data is anonymized and stripped of personal identifiers
- Opt out at any time (discount adjusts accordingly)
- Enterprise customers can negotiate custom data sharing agreements
- Premium tier data is used for training specialized research models

🔧 Looking for technical details? Check out our [Technical Documentation](TECHNICAL.md)

## 📋 Recent Updates

- **WebSocket Implementation**: Added real-time research updates via WebSockets
- **Enhanced Authentication**: Complete JWT token system with refresh capabilities and API key support
- **Subscription Features**: Implemented subscription-based access to premium features
- **GPU Acceleration**: Added optional GPU acceleration for faster research processing
- **Ollama Integration**: Added support for local model integration via Ollama (Privacy Plan)
- **Project Planning**: Created detailed [Action Plan](ACTION_PLAN.md) for remaining development tasks

## � Need Help?

Our support team is ready to assist you:
- 📧 support@parallaxanalytics.com
- 💬 Future LLM-supported/live chat support options on our website
- 📚 [Knowledge Base](https://docs.parallaxanalytics.com)

## 📄 License

© 2025 Parallax Analytics, LLC. All Rights Reserved.

Parallax Pal is proprietary software protected by copyright law. Unauthorized reproduction, distribution, or modification of this software, in whole or in part, is strictly prohibited.

This software is provided under a commercial license agreement and may only be used in accordance with the terms of that agreement. Use of this software constitutes acceptance of the Parallax Pal License Agreement which can be found at [https://parallaxanalytics.com/license](https://parallaxanalytics.com/license).

Parallax Pal incorporates certain open source components, each of which is governed by its respective license. A list of these components and their licenses can be found in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

For licensing inquiries, please contact licensing@parallaxanalytics.com.

## 💻 Development

### Getting Started

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your environment variables
3. Install backend dependencies: `pip install -r requirements.txt`
4. Install frontend dependencies: `cd src/frontend && npm install`
5. Start the backend server: `python -m src.api.main`
6. Start the frontend development server: `cd src/frontend && npm start`

### Docker Support

For containerized deployment:

```bash
docker-compose up -d
```

This will start both frontend and backend services as defined in `docker-compose.yml`.