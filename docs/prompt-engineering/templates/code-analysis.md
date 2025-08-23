# Code Analysis Prompt Templates

## 🔍 **Code Review Template**

### **Template Structure**
```markdown
Role: Senior Code Reviewer with [X years] experience in [Programming Language/Framework] and expertise in [Domain Area]

Context: [Project Type] codebase for [Business Domain]. Team size: [Number]. Development stage: [Alpha/Beta/Production]. Current focus: [Performance/Security/Maintainability/Scalability].

Code Under Review:
- **File/Module**: [Path/Name]
- **Function/Class**: [Specific component]
- **Lines of Code**: [Size/Scope]
- **Purpose**: [What this code is supposed to do]

Review Criteria:
- [Code standards compliance]
- [Performance considerations]
- [Security best practices]
- [Maintainability factors]
- [Testing coverage]

Task: [Comprehensive review/Focus on specific aspect/Pre-merge validation]

Constraints:
- [Time limitations]
- [Team skill level considerations]
- [Backward compatibility requirements]
- [Performance budget constraints]

Output Format:
1. **Issues Found** (Critical/Major/Minor with priority)
2. **Code Quality Assessment** (standards compliance)
3. **Recommendations** (specific improvements with code examples)
4. **Best Practices** (alignment with team standards)
5. **Approval Status** (approved/needs changes/rejected with reasoning)
```

### **Real Example: JavaScript Auto-Selection Fix**
```markdown
Role: Senior JavaScript Developer with 8+ years experience in vanilla JS and DOM manipulation with expertise in frontend state management

Context: License Plate Recognition (LPR) web application codebase for video surveillance. Team size: 2-3 developers. Development stage: Production with active users. Current focus: User experience improvement and bug fixes.

Code Under Review:
- **File/Module**: frontend/src/pages/RecordingsPage.js
- **Function/Class**: Auto-selection logic in renderCameraList() method
- **Lines of Code**: ~50 lines of camera selection and video loading
- **Purpose**: Automatically select and load videos for active cameras on page initialization

Review Criteria:
- DOM manipulation best practices
- Asynchronous operation handling
- State synchronization between UI and data
- Event handling patterns
- User experience consistency

Task: Review the auto-selection implementation focusing on timing synchronization between UI rendering and video loading

Constraints:
- Must maintain vanilla JS (no framework changes)
- Cannot break existing manual selection functionality
- Should follow established patterns in codebase
- Must work across different browsers

Output Format:
1. **Issues Found** (Critical/Major/Minor with priority)
2. **Code Quality Assessment** (standards compliance)
3. **Recommendations** (specific improvements with code examples)
4. **Best Practices** (alignment with team standards)
5. **Approval Status** (approved/needs changes/rejected with reasoning)
```

## 🏗️ **Architecture Analysis Template**

### **Template Structure**
```markdown
Role: Senior Software Architect with [X years] experience in [Technology Stack] and [Domain] systems

Context: [System Type] serving [User Base] with [Scale Requirements]. Current architecture: [High-level description]. Technology constraints: [Languages/Frameworks/Infrastructure].

System Components:
- **Frontend**: [Technology and responsibilities]
- **Backend Services**: [APIs and business logic]
- **Data Layer**: [Database and storage]
- **Infrastructure**: [Hosting and deployment]

Architecture Concerns:
- [Scalability requirements]
- [Performance expectations]
- [Security requirements]
- [Maintainability needs]
- [Integration requirements]

Task: [Evaluate current architecture/Propose improvements/Design new component/Migration planning]

Constraints:
- [Technical debt considerations]
- [Team expertise limitations]
- [Budget and timeline restrictions]
- [Business continuity requirements]

Output Format:
1. **Current State Analysis** (strengths and weaknesses)
2. **Architectural Issues** (technical debt and bottlenecks)
3. **Improvement Recommendations** (prioritized by impact)
4. **Implementation Roadmap** (phases and dependencies)
5. **Risk Assessment** (potential challenges and mitigations)
```

## 🐛 **Bug Analysis Template**

### **Template Structure**
```markdown
Role: Senior Debugging Specialist with expertise in [Technology Stack] and [System Type] troubleshooting

Context: [Application Type] experiencing [Bug Type] affecting [User Impact]. Occurrence pattern: [Frequency/Triggers]. System environment: [Development/Staging/Production].

Bug Description:
- **Symptom**: [What users experience]
- **Expected Behavior**: [What should happen]
- **Actual Behavior**: [What actually happens]
- **Reproduction Steps**: [How to trigger the bug]

Available Information:
- [Error messages/Stack traces]
- [Log file entries]
- [System state information]
- [User environment details]

Task: [Root cause analysis/Provide fix/Create test to prevent regression]

Constraints:
- [Time pressure for fix]
- [Impact on other system components]
- [Testing limitations]
- [Release schedule considerations]

Output Format:
1. **Root Cause Analysis** (technical explanation of why bug occurs)
2. **Impact Assessment** (user and system effects)
3. **Fix Implementation** (code changes with explanation)
4. **Testing Strategy** (verification and regression testing)
5. **Prevention Measures** (how to avoid similar bugs)
```

## ⚡ **Performance Analysis Template**

### **Template Structure**
```markdown
Role: Performance Engineering Specialist with expertise in [Technology Stack] optimization

Context: [Application Component] showing [Performance Issues] impacting [Business Metrics]. Current performance: [Metrics]. Target performance: [Goals]. System load: [Usage patterns].

Performance Symptoms:
- **Response Times**: [Current vs. Expected]
- **Resource Usage**: [CPU/Memory/Network/Disk]
- **Throughput**: [Requests/Transactions per time unit]
- **Error Rates**: [Timeouts/Failures]

Profiling Data:
- [Performance monitoring results]
- [Code profiling output]
- [Database query analysis]
- [Network latency measurements]

Task: [Identify bottlenecks/Optimize specific code/Implement caching/Scale solution]

Constraints:
- [Performance targets (SLA)]
- [Resource limitations]
- [Compatibility requirements]
- [Code change restrictions]

Output Format:
1. **Performance Bottleneck Analysis** (ranked by impact)
2. **Optimization Opportunities** (quick wins vs. long-term improvements)
3. **Code Changes Required** (specific optimizations with examples)
4. **Performance Testing Plan** (how to measure improvements)
5. **Monitoring Recommendations** (ongoing performance tracking)
```

## 🔒 **Security Code Review Template**

### **Template Structure**
```markdown
Role: Application Security Specialist with expertise in [Technology Stack] security vulnerabilities

Context: [Application Type] handling [Sensitive Data Types] requiring [Security Standards]. Security focus areas: [Authentication/Authorization/Data Protection/Input Validation].

Code Security Scope:
- **Component**: [Module/Function being reviewed]
- **Data Flow**: [How sensitive data moves through code]
- **User Input**: [Forms/APIs/File uploads]
- **External Integrations**: [Third-party services/APIs]

Security Checklist:
- [Input validation and sanitization]
- [Authentication and session management]
- [Authorization and access controls]
- [Data encryption and storage]
- [Error handling and information disclosure]

Task: [Security vulnerability assessment/Secure coding review/Compliance verification]

Constraints:
- [Compliance requirements (OWASP, NIST, etc.)]
- [Performance impact considerations]
- [User experience requirements]
- [Integration compatibility]

Output Format:
1. **Security Vulnerabilities** (critical/high/medium/low severity)
2. **Risk Assessment** (likelihood and business impact)
3. **Remediation Recommendations** (code fixes with examples)
4. **Security Testing Suggestions** (vulnerability testing approach)
5. **Security Controls Implementation** (preventive measures)
```

## 🧪 **Testing Code Analysis Template**

### **Template Structure**
```markdown
Role: Quality Assurance Engineer with expertise in [Testing Framework] and [Testing Strategy]

Context: [Application Component] requiring [Test Coverage Type]. Testing environment: [Unit/Integration/E2E]. Current coverage: [Percentage/Areas]. Testing constraints: [Time/Resources/Tools].

Code Testing Scope:
- **Functions/Methods**: [What needs testing]
- **Business Logic**: [Critical paths and edge cases]
- **Integration Points**: [External dependencies]
- **Error Conditions**: [Exception handling and error paths]

Testing Requirements:
- [Code coverage targets]
- [Performance testing needs]
- [Security testing requirements]
- [Accessibility testing needs]

Task: [Write comprehensive tests/Improve test coverage/Create testing strategy]

Constraints:
- [Testing framework limitations]
- [Test environment restrictions]
- [Execution time budgets]
- [Maintenance overhead considerations]

Output Format:
1. **Test Coverage Analysis** (current gaps and needs)
2. **Test Strategy Recommendations** (approach and priorities)
3. **Test Implementation** (specific test cases with code)
4. **Test Automation** (CI/CD integration approach)
5. **Quality Metrics** (how to measure testing effectiveness)
```

## 📋 **Template Usage Guidelines**

### **Choosing the Right Template**
- **Code Review**: Pre-merge reviews, quality assessments
- **Architecture Analysis**: System design evaluation, technical debt assessment
- **Bug Analysis**: Production issues, user-reported problems
- **Performance Analysis**: Slow operations, scalability issues
- **Security Review**: Vulnerability assessment, compliance checks
- **Testing Analysis**: Test coverage improvement, quality assurance

### **Customization Best Practices**
1. **Specify exact technology stack** (versions matter)
2. **Include quantitative metrics** where possible
3. **Define clear success criteria** for recommendations
4. **Consider team skill levels** in constraint section
5. **Add business context** for prioritization decisions

### **Template Refinement Process**
1. Start with base template for your scenario
2. Customize all bracketed placeholders
3. Add domain-specific context and requirements
4. Test with real code samples
5. Refine based on response quality and completeness
6. Save successful variations for reuse
7. Share refined templates with development team