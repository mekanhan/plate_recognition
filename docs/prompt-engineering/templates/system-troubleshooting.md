# System Troubleshooting Prompt Templates

## 🔧 **Connection Issues Template**

### **Template Structure**
```markdown
Role: System Network Diagnostician with 10+ years experience in [Web Applications/API Services/Database Systems]

Context: [System Description] experiencing [Specific Connection Issue] affecting [User Impact]. System architecture includes [Key Components]. Error pattern: [Frequency/Triggers/Conditions].

Current Symptoms:
- [Specific error messages]
- [Performance metrics/logs]
- [User-reported behaviors]
- [System resource status]

Available Information:
- [Log files/Error traces]
- [System monitoring data]  
- [Network configuration]
- [Recent changes/deployments]

Task: [Diagnose root cause/Provide immediate fix/Create prevention strategy]

Constraints:
- [Downtime limitations]
- [Available maintenance windows] 
- [Team skill levels]
- [System dependencies]

Output Format:
1. **Root Cause Analysis** (3-5 key factors)
2. **Immediate Actions** (emergency fixes)
3. **Permanent Solution** (code/config changes)
4. **Prevention Measures** (monitoring/alerts)
5. **Testing Verification** (steps to confirm fix)
```

### **Real Example: ERR_CONNECTION_RESET**
```markdown
Role: System Network Diagnostician with 10+ years experience in Node.js web applications and database connectivity

Context: License Plate Recognition (LPR) system experiencing frequent ERR_CONNECTION_RESET errors affecting user interface functionality. System architecture includes FastAPI backend (port 8001), Recording Service (port 8002), and SQLite database with connection pooling. Error pattern occurs every 2-3 minutes during normal operations.

Current Symptoms:
- Frontend API calls failing with "net::ERR_CONNECTION_RESET"
- Database connection errors: "Cannot operate on a closed database"
- Services restart frequently (every 10-15 minutes)
- Users report interface freezing and loading states

Available Information:
- API logs showing SQLite connection errors
- Background monitoring tasks failing
- No connection retry logic in frontend
- Services using separate database sessions

Task: Diagnose root cause and implement comprehensive fix for connection stability

Constraints:
- Zero downtime requirement
- Must maintain existing API compatibility
- Team familiar with JavaScript/Python only
- Cannot change database engine (SQLite required)

Output Format:
1. **Root Cause Analysis** (3-5 key factors)
2. **Immediate Actions** (emergency fixes)
3. **Permanent Solution** (code/config changes)
4. **Prevention Measures** (monitoring/alerts)
5. **Testing Verification** (steps to confirm fix)
```

## ⚡ **Performance Issues Template**

### **Template Structure**
```markdown
Role: Performance Optimization Specialist with expertise in [Technology Stack]

Context: [Application Type] experiencing [Performance Issues] impacting [Business Metrics]. Current architecture: [System Components]. Performance baseline: [Current metrics vs. Expected metrics].

Performance Symptoms:
- [Response times/Throughput metrics]
- [Resource utilization (CPU/Memory/Disk)]
- [User experience impacts]
- [Error rates/Timeouts]

Profiling Data:
- [Application performance metrics]
- [Database query performance]
- [Network latency measurements]
- [Resource bottlenecks identified]

Task: [Identify bottlenecks/Optimize specific component/Implement caching strategy]

Constraints:
- [Performance targets (SLA requirements)]
- [Resource limitations (budget/hardware)]
- [Compatibility requirements]
- [Change management restrictions]

Output Format:
1. **Bottleneck Analysis** (ranked by impact)
2. **Quick Wins** (immediate improvements)
3. **Optimization Plan** (systematic improvements)
4. **Implementation Roadmap** (phases and timeline)
5. **Success Metrics** (how to measure improvement)
```

## 🗄️ **Database Issues Template**

### **Template Structure**
```markdown
Role: Database Performance Specialist with [X years] experience in [Database Technology]

Context: [Application] using [Database System] experiencing [Database Issues]. Database size: [Records/Storage]. Transaction volume: [Ops/second]. Current configuration: [Key settings].

Database Symptoms:
- [Query performance issues]
- [Connection pool problems]
- [Lock contention/Deadlocks]
- [Storage/Memory utilization]

Diagnostic Information:
- [Slow query logs]
- [Connection statistics]
- [Index usage reports]
- [Database error logs]

Task: [Optimize queries/Fix connection issues/Implement proper indexing/Resolve locking problems]

Constraints:
- [Maintenance window availability]
- [Data integrity requirements]
- [Application compatibility needs]
- [Performance SLA requirements]

Output Format:
1. **Issue Classification** (immediate vs. systemic)
2. **Emergency Fixes** (critical path solutions)
3. **Optimization Strategy** (systematic improvements)
4. **Monitoring Setup** (proactive alerting)
5. **Maintenance Plan** (ongoing health management)
```

## 🖥️ **UI/Frontend Issues Template**

### **Template Structure**
```markdown
Role: Senior Frontend Developer specializing in [Framework/Vanilla JS] with expertise in [UI/UX patterns]

Context: [Application Type] with [User Base] experiencing [Frontend Issues]. Technology stack: [Frontend technologies]. Browser support: [Target browsers]. Current user flow: [Key user interactions].

User Experience Issues:
- [Loading problems/Performance]
- [Interaction failures (clicks, forms)]
- [Visual rendering problems]
- [Mobile/responsive issues]

Available Information:
- [Browser console errors]
- [User agent analytics]
- [Performance profiling data]
- [User feedback/bug reports]

Task: [Fix interaction bugs/Improve loading performance/Resolve display issues/Enhance user experience]

Constraints:
- [Browser compatibility requirements]
- [Framework/library limitations]
- [Design system requirements]
- [Accessibility standards]

Output Format:
1. **Issue Root Cause** (technical explanation)
2. **User Impact Assessment** (severity and scope)
3. **Technical Solution** (code changes required)
4. **Testing Strategy** (verification steps)
5. **User Experience Improvement** (before/after comparison)
```

## 🔒 **Security Issues Template**

### **Template Structure**
```markdown
Role: Security Engineer with expertise in [Web Application Security/Infrastructure Security]

Context: [System Type] with [Sensitive Data Types] requiring [Security Standards Compliance]. Current security posture: [Known measures]. Threat landscape: [Relevant threats for this system type].

Security Concerns:
- [Identified vulnerabilities]
- [Access control issues]
- [Data exposure risks]
- [Authentication/Authorization gaps]

Security Assessment Data:
- [Vulnerability scan results]
- [Penetration test findings]
- [Security audit reports]
- [Compliance gap analysis]

Task: [Address specific vulnerabilities/Implement security controls/Create security monitoring/Establish compliance]

Constraints:
- [Compliance requirements (GDPR, HIPAA, etc.)]
- [Business continuity needs]
- [User experience requirements]
- [Budget/resource limitations]

Output Format:
1. **Risk Assessment** (threat level and business impact)
2. **Immediate Security Measures** (critical fixes)
3. **Security Implementation Plan** (systematic improvements)
4. **Monitoring and Detection** (security alerting setup)
5. **Compliance Verification** (audit trail and documentation)
```

## 📋 **Template Usage Guidelines**

### **When to Use Each Template**
- **Connection Issues**: ERR_CONNECTION_RESET, timeouts, service unavailable
- **Performance Issues**: Slow responses, high resource usage, scalability problems  
- **Database Issues**: Slow queries, connection pool exhaustion, data integrity
- **UI/Frontend Issues**: Loading problems, interaction failures, display bugs
- **Security Issues**: Vulnerabilities, access control, compliance gaps

### **Customization Tips**
1. **Replace bracketed placeholders** with specific details
2. **Adjust constraint priorities** based on your situation
3. **Modify output format** to match your documentation needs
4. **Add domain-specific context** relevant to your system
5. **Include quantitative metrics** where possible

### **Template Evolution**
- Start with base template
- Customize for your specific domain
- Test with real issues  
- Refine based on response quality
- Save successful variations
- Share improvements with team