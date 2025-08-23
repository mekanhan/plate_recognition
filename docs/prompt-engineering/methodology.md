# Systematic Prompt Engineering Methodology

## 🎯 **The Universal 5-Step Refinement Process**

**Golden Rule**: Always start with a basic prompt, then refine systematically.

### **Step 1: Start Basic/Draft**
Begin with the simplest possible request:
```
"Fix this bug"
"Optimize this code" 
"Design this system"
```

### **Step 2: Add Role/Persona** 
Define who should answer:
```
"As a senior software engineer, fix this bug"
"As a performance optimization expert, optimize this code"
"As a system architect, design this system"
```

### **Step 3: Add Context (Background/Domain)**
Provide relevant background:
```
"As a senior software engineer working on a legacy JavaScript/Node.js LPR system, 
fix this connection reset bug that occurs during high traffic periods..."
```

### **Step 4: Add Constraints (Length/Style/Limits)**
Specify boundaries:
```
"...Provide a concise solution under 200 lines, focusing on production stability 
without breaking existing functionality..."
```

### **Step 5: Specify Output Format**
Define the desired response structure:
```
"...Format your response as:
1. Root cause analysis (max 3 bullet points)
2. Code solution with comments
3. Testing steps to verify the fix"
```

## 📝 **Complete Example Evolution**

### **❌ Poor Prompt (Original)**
```
"The video won't load when camera is auto-selected"
```

### **✅ Engineered Prompt (After 5 Steps)**
```
Role: Senior Frontend Developer specializing in JavaScript/ES6 and video streaming applications

Context: Working on a license plate recognition (LPR) system with a recordings page that auto-selects cameras on page load. The system uses vanilla JavaScript, has 114 video segments available, and integrates with a recording service API on port 8002. Users report that auto-selected cameras show checkmarks but videos remain stuck in loading state, while manual selection works perfectly.

Task: Diagnose and fix the video loading synchronization issue between auto-selection state management and video playback initialization.

Constraints: 
- Must maintain existing UI/UX patterns
- No framework changes allowed (vanilla JS only)
- Solution should be under 50 lines of code changes
- Must not break manual selection functionality

Output Format:
1. **Root Cause Analysis** (3-5 bullet points)
2. **Solution Code** (with line-by-line comments)
3. **Verification Steps** (3 specific tests to confirm fix)
4. **Expected User Experience** (before/after comparison)
```

## 🛠️ **Domain-Specific Prompt Templates**

### **System Troubleshooting Template**
```markdown
Role: [System Diagnostician/DevOps Engineer/Performance Analyst]
Context: [System Type] experiencing [Symptoms] in [Environment]
Current State: [Error logs/Metrics/User reports]
Available Resources: [Tools/Access/Time constraints]
Task: [Specific diagnostic or fix request]
Constraints: [Downtime limits/Budget/Compatibility requirements]
Format: 
- Root cause analysis
- Step-by-step solution
- Prevention measures
- Monitoring recommendations
```

### **Code Review Template**
```markdown
Role: Senior Code Reviewer with [X years] experience in [Technology Stack]
Context: [Project type] codebase, [Team size], [Performance/Security/Maintainability] focus
Code Under Review: [File/Function/Module description]
Review Criteria: [Standards/Guidelines/Performance metrics]
Task: Comprehensive code review focusing on [Specific aspects]
Constraints: [Timeline/Scope/Priority level]
Format:
- Issues (Critical/Major/Minor)
- Recommendations with code examples
- Best practices alignment
- Approval status with reasoning
```

### **Architecture Design Template**
```markdown
Role: Senior System Architect with expertise in [Domain/Technologies]
Context: [Business requirements], [Scale expectations], [Current constraints]
Existing System: [Current architecture overview]
Requirements: [Functional/Non-functional requirements]
Task: [Design/Redesign/Integration] request
Constraints: [Budget/Timeline/Technology stack/Team skills]
Format:
- Architecture diagram (text description)
- Component breakdown
- Data flow description
- Implementation roadmap
- Risk assessment
```

## 📊 **Template Selection Guide**

| Scenario | Template | Key Focus |
|----------|----------|-----------|
| Bug Reports | Troubleshooting | Root cause + Fix |
| Performance Issues | System Analysis | Metrics + Optimization |
| Feature Requests | Architecture Design | Requirements + Implementation |
| Code Quality | Code Review | Standards + Best practices |
| User Experience | UX Analysis | User journey + Improvements |
| Security Concerns | Security Audit | Vulnerabilities + Mitigations |
| Documentation Needs | Technical Writing | Clarity + Completeness |

## 🎯 **Quality Indicators**

### **Good Prompt Characteristics**
- ✅ **Specific role** clearly defined
- ✅ **Sufficient context** for understanding
- ✅ **Clear constraints** and limitations
- ✅ **Defined output format** 
- ✅ **Actionable task** description

### **Poor Prompt Red Flags**
- ❌ Vague or generic requests
- ❌ Missing context or background
- ❌ No output format specified
- ❌ Unclear success criteria
- ❌ No role/expertise defined

## 🔄 **Iterative Improvement Process**

### **When to Refine Further**
1. **Response too generic** → Add more specific context
2. **Wrong format** → Clarify output requirements
3. **Missing key points** → Expand role expertise
4. **Over-complicated** → Add simplicity constraints
5. **Incomplete solution** → Specify completeness criteria

### **Template Evolution**
1. **Start** with basic template
2. **Test** with real scenarios
3. **Refine** based on results
4. **Save** successful variations
5. **Share** with team for feedback

## 💡 **Best Practices**

### **Do's**
- Start simple, build complexity gradually
- Save successful prompts as templates
- Include specific examples in context
- Define clear success criteria
- Test templates with different scenarios

### **Don'ts**  
- Don't over-engineer initial prompts
- Don't skip the role definition
- Don't forget output format specification
- Don't ignore constraint requirements
- Don't use templates without customization

## 🚀 **Implementation Checklist**

- [ ] Identify common prompt scenarios in your domain
- [ ] Create base templates for each scenario
- [ ] Test templates with real problems
- [ ] Refine based on response quality
- [ ] Document successful patterns
- [ ] Share templates with team
- [ ] Establish template review process
- [ ] Create template versioning system

This methodology transforms ad-hoc prompting into a systematic, repeatable process that consistently produces high-quality, actionable responses across all technical domains.