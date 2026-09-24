/**
 * Apex Sentinel • Fraud Operations Console
 * Interactive TigerGraph Visualizer, Case Dossier & Conversational Co-Pilot.
 */

document.addEventListener("DOMContentLoaded", () => {
    let allCases = [];
    let activeCase = null;
    let currentFilter = "ALL";
    let searchQuery = "";
    let simulation = null;
    let svg = null;
    let g = null;
    let lastGraphData = null;

    // Customer Persona Mapping to make cases human-centered
    const PERSONAS = {
        "CUST_5011": { name: "Sarah Jenkins", tenure: "Customer for 4.2 years", location: "Seattle, WA", segment: "Preferred Banking • 745 FICO", avatar: "SJ" },
        "CUST_5012": { name: "Marcus Rivera", tenure: "Customer for 2.8 years", location: "New York, NY", segment: "Commercial Business • 780 FICO", avatar: "MR" },
        "CUST_5013": { name: "Elena Vance", tenure: "Customer for 5.1 years", location: "San Francisco, CA", segment: "Private Client • 810 FICO", avatar: "EV" },
        "CUST_5014": { name: "Jordan Brooks", tenure: "New Account (34 days)", location: "Atlanta, GA", segment: "Standard Checking • Thin File", avatar: "JB" },
        "CUST_5015": { name: "Tyler Harrison", tenure: "Customer for 6 months", location: "Dallas, TX", segment: "Credit Builder • 620 FICO", avatar: "TH" },
        "CUST_5016": { name: "Chloe Martinez", tenure: "Customer for 1.5 years", location: "Miami, FL", segment: "Consumer Checking • 690 FICO", avatar: "CM" },
        "CUST_5017": { name: "Robert Taylor", tenure: "Customer for 8.3 years", location: "Denver, CO", segment: "Premier Wealth • 825 FICO", avatar: "RT" },
        "CUST_5018": { name: "Avery Chen", tenure: "New Account (12 days)", location: "Chicago, IL", segment: "Digital Checking • Unverified", avatar: "AC" },
        "CUST_5019": { name: "Hannah Kim", tenure: "Customer for 3.6 years", location: "Portland, OR", segment: "Preferred Banking • 760 FICO", avatar: "HK" },
        "CUST_5020": { name: "Liam O'Connor", tenure: "Customer for 7 months", location: "Phoenix, AZ", segment: "Revolving Line • 640 FICO", avatar: "LO" }
    };

    function getPersona(id) {
        return PERSONAS[id] || {
            name: `Cardholder ${id}`,
            tenure: "Verified Account • 3+ years",
            location: "United States",
            segment: "Active Consumer Banking",
            avatar: id.replace("CUST_", "").slice(0, 2)
        };
    }

    // Elements
    const caseListEl = document.getElementById("case-list");
    const activeCaseIdEl = document.getElementById("active-case-id");
    const activeCaseTitleEl = document.getElementById("active-case-title");
    const riskBadgeEl = document.getElementById("risk-score-badge");
    const riskScoreValEl = document.getElementById("risk-score-value");
    const graphContainer = document.getElementById("graph-container");
    const tooltipEl = document.getElementById("graph-tooltip");
    const tgCountsEl = document.getElementById("graph-counts");

    // Dossier Elements
    const dossierCustomerName = document.getElementById("dossier-customer-name");
    const dossierCustomerSub = document.getElementById("dossier-customer-sub");
    const customerAvatarInitials = document.getElementById("customer-avatar-initials");
    const dossierAmount = document.getElementById("dossier-amount");
    const dossierChannel = document.getElementById("dossier-channel");
    const dossierAccount = document.getElementById("dossier-account");
    const dossierLocation = document.getElementById("dossier-location");
    const dossierDistance = document.getElementById("dossier-distance");
    const dossierPattern = document.getElementById("dossier-pattern");
    const dossierStatus = document.getElementById("dossier-status");
    const graphDiscoveryText = document.getElementById("graph-discovery-text");

    // Briefing Elements
    const humanStoryText = document.getElementById("human-story-text");
    const humanEmpathyText = document.getElementById("human-empathy-text");
    const customerSmsPreview = document.getElementById("customer-sms-preview");
    const supportScriptText = document.getElementById("support-script-text");

    // NBA & SAR elements
    const nbaPreActionEl = document.getElementById("nba-pre-action");
    const nbaPreRationaleEl = document.getElementById("nba-pre-rationale");
    const nbaPreRouteEl = document.getElementById("nba-pre-route");
    const nbaPostActionEl = document.getElementById("nba-post-action");
    const nbaPostRationaleEl = document.getElementById("nba-post-rationale");
    const nbaPostRouteEl = document.getElementById("nba-post-route");
    const governanceBadgeEl = document.getElementById("governance-badge");
    const sarTextEl = document.getElementById("sar-text");
    const precedentListEl = document.getElementById("precedent-list");

    // Copilot Elements
    const copilotInput = document.getElementById("copilot-input");
    const btnSendCopilot = document.getElementById("btn-send-copilot");
    const copilotMessages = document.getElementById("copilot-messages");

    // Search Input
    const searchInput = document.getElementById("case-search-input");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            searchQuery = e.target.value.toLowerCase().trim();
            renderCaseList();
        });
    }

    // -------------------------------------------------------------------------
    // 1. Initial Load & Setup
    // -------------------------------------------------------------------------
    fetchSystemStatus();
    loadCases();

    // Filter Pills
    document.querySelectorAll(".filter-pill").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".filter-pill").forEach(b => b.classList.remove("active"));
            e.target.classList.add("active");
            currentFilter = e.target.dataset.filter;
            renderCaseList();
        });
    });

    // Reset / Fit graph button
    const resetGraphBtn = document.getElementById("btn-reset-graph");
    if (resetGraphBtn) {
        resetGraphBtn.addEventListener("click", () => {
            if (activeCase) {
                loadCaseSubgraph(activeCase.case_id);
            }
        });
    }

    // Nav Tab: Entity Graph (Direct Jump & Highlight)
    const navTabGraph = document.getElementById("nav-tab-graph");
    if (navTabGraph) {
        navTabGraph.addEventListener("click", (e) => {
            e.preventDefault();
            const graphCard = document.getElementById("graph-card");
            if (graphCard) {
                graphCard.scrollIntoView({ behavior: "smooth", block: "center" });
                graphCard.classList.add("highlight-focus");
                setTimeout(() => graphCard.classList.remove("highlight-focus"), 2000);
            }
            if (lastGraphData) {
                renderD3Graph(lastGraphData);
            }
        });
    }

    // Nav Tab: Queue
    const navTabQueue = document.getElementById("nav-tab-queue");
    if (navTabQueue) {
        navTabQueue.addEventListener("click", (e) => {
            e.preventDefault();
            const mainWork = document.querySelector(".workspace-center");
            if (mainWork) mainWork.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    // Toggle Expanded Graph Canvas
    const toggleExpandBtn = document.getElementById("btn-toggle-expand-graph");
    if (toggleExpandBtn) {
        toggleExpandBtn.addEventListener("click", () => {
            const graphCard = document.getElementById("graph-card");
            const btnText = document.getElementById("expand-btn-text");
            if (graphCard) {
                graphCard.classList.toggle("expanded");
                const isExpanded = graphCard.classList.contains("expanded");
                if (btnText) btnText.textContent = isExpanded ? "Collapse" : "Expand";
                setTimeout(() => {
                    if (lastGraphData) renderD3Graph(lastGraphData);
                }, 310);
            }
        });
    }

    // Re-investigate button
    document.getElementById("btn-reinvestigate").addEventListener("click", () => {
        if (activeCase) {
            runInvestigation(activeCase.case_id);
        }
    });

    // Simulate Evidence Button
    document.getElementById("btn-simulate-event").addEventListener("click", () => {
        if (!activeCase) return;
        const selectedChoice = document.querySelector('input[name="sim_choice"]:checked').value;
        const simulatedEvidence = {
            step_up_result: selectedChoice === "LEGITIMATE_PURCHASE" ? "PASSED" : "FAILED_OR_EXPIRED",
            customer_confirmation: selectedChoice
        };
        runInvestigation(activeCase.case_id, simulatedEvidence);
    });

    // Copy SAR Narrative
    document.getElementById("btn-copy-sar").addEventListener("click", () => {
        const text = sarTextEl.textContent;
        navigator.clipboard.writeText(text).then(() => {
            alert("Official FinCEN SAR narrative copied to clipboard!");
        });
    });

    // Export Answer JSON
    document.getElementById("btn-download-answer").addEventListener("click", () => {
        if (!activeCase || !activeCase.answer) return;
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(activeCase.answer, null, 2));
        const downloadAnchor = document.createElement("a");
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `case_${activeCase.case_id.toLowerCase()}_answer.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    });

    // Re-evaluate Benchmark
    document.getElementById("btn-run-all-benchmarks").addEventListener("click", async () => {
        caseListEl.innerHTML = '<div class="loading-state">Re-evaluating benchmark suite across TigerGraph...</div>';
        try {
            await fetch("/api/benchmark/summary");
            await loadCases();
        } catch (err) {
            console.error("Error re-running:", err);
        }
    });

    // -------------------------------------------------------------------------
    // 2. Data Fetching
    // -------------------------------------------------------------------------
    async function fetchSystemStatus() {
        try {
            const res = await fetch("/api/tigergraph/status");
            const data = await res.json();
            if (tgCountsEl) tgCountsEl.textContent = `${data.total_vertices} Nodes • ${data.total_edges} Edges`;
        } catch (err) {
            console.error("Status error:", err);
        }
    }

    async function loadCases() {
        try {
            const res = await fetch("/api/cases");
            allCases = await res.json();
            renderCaseList();
            if (allCases.length > 0) {
                selectCase(allCases[0].case_id);
            }
        } catch (err) {
            caseListEl.innerHTML = '<div class="error-msg">Failed to load cases queue.</div>';
        }
    }

    function renderCaseList() {
        caseListEl.innerHTML = "";
        const filtered = allCases.filter(c => {
            // Tab filter
            let tabMatch = true;
            if (currentFilter === "FRAUD") tabMatch = c.status.includes("FRAUD");
            else if (currentFilter === "CLEARED") tabMatch = c.status.includes("CLEARED");
            else if (currentFilter === "SAR") tabMatch = c.sar_filed === true;

            // Search filter
            let textMatch = true;
            if (searchQuery) {
                const persona = getPersona(c.customer_id || "");
                textMatch = c.case_id.toLowerCase().includes(searchQuery) ||
                            c.title.toLowerCase().includes(searchQuery) ||
                            persona.name.toLowerCase().includes(searchQuery) ||
                            String(c.amount).includes(searchQuery);
            }

            return tabMatch && textMatch;
        });

        filtered.forEach(c => {
            const card = document.createElement("div");
            card.className = `case-card ${activeCase && activeCase.case_id === c.case_id ? "active" : ""}`;
            
            let badgeClass = "badge-danger";
            if (c.status.includes("CLEARED")) badgeClass = "badge-success";
            else if (c.status.includes("PENDING")) badgeClass = "badge-info";

            const persona = getPersona(c.customer_id || `CUST_${c.case_index + 5010}`);

            card.innerHTML = `
                <div class="case-card-header">
                    <span class="case-card-id">${c.case_id}</span>
                    <span class="badge ${badgeClass}">${c.status.replace("CLOSED_", "")}</span>
                </div>
                <div class="case-card-title">${c.title}</div>
                <div class="case-card-footer">
                    <span>${persona.name} • $${Number(c.amount).toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                    <span>${c.sar_filed ? "🚨 SAR" : "Score: " + Math.round(c.assessed_risk_score)}</span>
                </div>
            `;

            card.addEventListener("click", () => selectCase(c.case_id));
            caseListEl.appendChild(card);
        });
    }

    async function selectCase(caseId) {
        try {
            const res = await fetch(`/api/cases/${caseId}`);
            const data = await res.json();
            activeCase = {
                case_id: caseId,
                benchmark: data.benchmark_case,
                answer: data.answer
            };

            updateCaseUI();
            loadCaseSubgraph(caseId);
            renderCaseList();
        } catch (err) {
            console.error("Error selecting case:", err);
        }
    }

    async function runInvestigation(caseId, simulatedEvidence = null) {
        try {
            const btn = document.getElementById("btn-reinvestigate");
            if (btn) btn.textContent = "Analyzing...";
            const res = await fetch("/api/investigate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    case_id: caseId,
                    simulated_evidence: simulatedEvidence
                })
            });
            const answer = await res.json();
            activeCase.answer = answer;
            updateCaseUI();
            loadCaseSubgraph(caseId);
            fetchSystemStatus();
            if (btn) {
                btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run Investigation`;
            }
        } catch (err) {
            console.error("Investigation error:", err);
        }
    }

    // -------------------------------------------------------------------------
    // 3. UI Updates & Persona Mapping
    // -------------------------------------------------------------------------
    function updateCaseUI() {
        if (!activeCase || !activeCase.answer) return;
        const ans = activeCase.answer;
        const sum = ans.case_summary;
        const nba = ans.next_best_action;
        const sar = ans.suspicious_activity_report;
        const inv = ans.investigation_record;
        const human = ans.humanized_briefing || {};
        const outreach = ans.customer_outreach || {};

        // Persona Information
        const custId = sum.customer_id || (activeCase.benchmark && activeCase.benchmark.customer_id) || "CUST_5011";
        const persona = getPersona(custId);

        // Header / Breadcrumb
        activeCaseIdEl.textContent = sum.case_id;
        activeCaseTitleEl.textContent = (activeCase.benchmark && activeCase.benchmark.title) || `Case ${sum.case_id}`;

        // Risk Meter
        const riskScore = Math.round(sum.assessed_risk_score);
        riskScoreValEl.textContent = `${riskScore} / 100`;
        if (riskScore < 50) {
            riskBadgeEl.className = "risk-meter-chip cleared";
        } else {
            riskBadgeEl.className = "risk-meter-chip";
        }

        // Customer Dossier Strip
        if (dossierCustomerName) dossierCustomerName.textContent = `${persona.name} (${custId})`;
        if (dossierCustomerSub) dossierCustomerSub.textContent = `${persona.tenure} • ${persona.segment}`;
        if (customerAvatarInitials) customerAvatarInitials.textContent = persona.avatar;
        if (dossierAmount) dossierAmount.textContent = `$${Number(sum.amount).toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        if (dossierAccount) dossierAccount.textContent = `Checking Account • ${sum.account_id}`;
        if (dossierPattern) dossierPattern.textContent = sum.detected_pattern;
        if (dossierStatus) dossierStatus.textContent = `Status: ${sum.status.replace("CLOSED_", "")}`;

        // Location / Observed Environment
        const distance = (inv && inv.graph_findings && inv.graph_findings[0]) ? inv.graph_findings[0] : "";
        if (graphDiscoveryText) graphDiscoveryText.textContent = distance || "Normal transactional parameters observed.";

        // Humanized Story & Empathy Briefing
        if (humanStoryText) humanStoryText.textContent = human.story || "No briefing available.";
        if (humanEmpathyText) humanEmpathyText.textContent = human.empathy_assessment || "";

        // Customer Outreach & Script
        if (customerSmsPreview) customerSmsPreview.textContent = outreach.sms_text || "";
        if (supportScriptText) supportScriptText.textContent = outreach.support_agent_greeting || "";

        // NBA Pre & Post
        nbaPreActionEl.textContent = nba.before_additional_evidence.recommended_action;
        nbaPreRationaleEl.textContent = nba.before_additional_evidence.rationale;
        nbaPreRouteEl.textContent = nba.before_additional_evidence.required_approval_route;

        nbaPostActionEl.textContent = nba.after_additional_evidence.recommended_action;
        nbaPostRationaleEl.textContent = nba.after_additional_evidence.rationale;
        nbaPostRouteEl.textContent = nba.after_additional_evidence.required_approval_route;

        governanceBadgeEl.textContent = nba.after_additional_evidence.required_approval_route;

        // SAR Report Section
        if (typeof sar === "object" && sar.fincen_narrative) {
            sarTextEl.textContent = sar.fincen_narrative;
            document.getElementById("sar-badge").textContent = "31 CFR § 1020.320 (FILED)";
            document.getElementById("sar-badge").className = "badge badge-danger";
        } else {
            sarTextEl.textContent = "SUSPICIOUS ACTIVITY REPORT NOT REQUIRED\nActivity is within approved customer risk tolerance or below mandatory filing thresholds.";
            document.getElementById("sar-badge").textContent = "EXEMPT";
            document.getElementById("sar-badge").className = "badge badge-success";
        }

        // Case Memory Precedents
        precedentListEl.innerHTML = "";
        (inv.case_memory_precedents || []).forEach(p => {
            const item = document.createElement("div");
            item.className = "precedent-card";
            item.innerHTML = `
                <div class="prec-head">
                    <span class="prec-id">${p.precedent_case_id}</span>
                    <span class="prec-match text-success">${Math.round(p.similarity * 100)}% Match</span>
                </div>
                <div class="prec-body">Outcome: <strong>${p.prior_outcome}</strong> (${p.prior_decision})</div>
            `;
            precedentListEl.appendChild(item);
        });
    }

    // -------------------------------------------------------------------------
    // 4. Interactive Co-Pilot Chat
    // -------------------------------------------------------------------------
    async function sendCopilotMessage() {
        const text = copilotInput.value.trim();
        if (!text || !activeCase) return;

        // User message bubble
        const userMsg = document.createElement("div");
        userMsg.className = "copilot-msg user";
        userMsg.innerHTML = `<div class="msg-author" style="color:#e2e8f0;text-align:right;">You (Investigator)</div><div>${text}</div>`;
        copilotMessages.appendChild(userMsg);
        copilotInput.value = "";
        copilotMessages.scrollTop = copilotMessages.scrollHeight;

        try {
            const res = await fetch("/api/copilot/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    case_id: activeCase.case_id,
                    message: text
                })
            });
            const data = await res.json();
            const agentMsg = document.createElement("div");
            agentMsg.className = "copilot-msg agent";
            agentMsg.innerHTML = `<div class="msg-author">Apex Co-Pilot</div><div>${data.reply.replace(/\n/g, "<br>")}</div>`;
            copilotMessages.appendChild(agentMsg);
            copilotMessages.scrollTop = copilotMessages.scrollHeight;
        } catch (err) {
            console.error("Copilot chat error:", err);
        }
    }

    if (btnSendCopilot) btnSendCopilot.addEventListener("click", sendCopilotMessage);
    if (copilotInput) {
        copilotInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") sendCopilotMessage();
        });
    }

    // -------------------------------------------------------------------------
    // 5. Refined D3 Force Graph Canvas
    // -------------------------------------------------------------------------
    async function loadCaseSubgraph(caseId) {
        try {
            const txnId = activeCase.benchmark ? activeCase.benchmark.transaction.transaction_id : caseId;
            const res = await fetch(`/api/graph/subgraph/${txnId}?hops=2`);
            const graphData = await res.json();
            lastGraphData = graphData;
            renderD3Graph(graphData);
        } catch (err) {
            console.error("Subgraph fetch error:", err);
        }
    }

    function renderD3Graph(data) {
        if (!data || !data.nodes) return;
        lastGraphData = data;
        graphContainer.innerHTML = "";
        const width = Math.max(graphContainer.clientWidth || 0, 600);
        const height = Math.max(graphContainer.clientHeight || 0, 260);

        if (typeof d3 === "undefined") {
            renderFallbackSVG(data, width, height);
            return;
        }

        svg = d3.select("#graph-container")
            .append("svg")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("viewBox", [0, 0, width, height]);

        g = svg.append("g");
        const zoom = d3.zoom()
            .scaleExtent([0.3, 3])
            .on("zoom", (event) => g.attr("transform", event.transform));
        svg.call(zoom);

        const nodes = data.nodes.map(d => ({ ...d }));
        const links = data.edges.map(d => ({ ...d }));

        simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(85))
            .force("charge", d3.forceManyBody().strength(-240))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(26));

        // Links
        const link = g.append("g")
            .attr("stroke", "#374151")
            .attr("stroke-opacity", 0.6)
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("stroke-width", 1.5)
            .attr("stroke-dasharray", "4,2");

        // Nodes
        const node = g.append("g")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        // Circle
        node.append("circle")
            .attr("r", d => d.type === "Transaction" ? 14 : 11)
            .attr("fill", d => getNodeColor(d.type))
            .attr("stroke", "#ffffff")
            .attr("stroke-width", 1.5)
            .attr("cursor", "pointer");

        // Label
        node.append("text")
            .text(d => d.label)
            .attr("x", 16)
            .attr("y", 4)
            .attr("fill", "#e5e7eb")
            .attr("font-size", "10px")
            .attr("font-family", "Inter, sans-serif")
            .attr("font-weight", "500");

        // Tooltip
        node.on("mouseover", (event, d) => {
            tooltipEl.style.display = "block";
            tooltipEl.style.left = (event.offsetX + 15) + "px";
            tooltipEl.style.top = (event.offsetY - 20) + "px";
            tooltipEl.innerHTML = `
                <div style="font-weight:700;color:${getNodeColor(d.type)}">${d.type}: ${d.label}</div>
                <div style="font-size:10px;margin-top:2px;color:#9ca3af;">Entity ID: ${d.id}</div>
            `;
        }).on("mouseout", () => {
            tooltipEl.style.display = "none";
        });

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${d.x},${d.y})`);
        });

        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }

        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }

        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }
    }

    function renderFallbackSVG(data, width, height) {
        const svgEl = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svgEl.setAttribute("width", "100%");
        svgEl.setAttribute("height", "100%");
        svgEl.setAttribute("viewBox", `0 0 ${width} ${height}`);

        const cx = width / 2;
        const cy = height / 2;
        const radius = Math.min(width, height) * 0.35;

        // Position nodes
        const nodePositions = {};
        const total = data.nodes.length;
        data.nodes.forEach((n, idx) => {
            if (n.type === "Transaction") {
                nodePositions[n.id] = { x: cx, y: cy };
            } else {
                const angle = (idx / total) * 2 * Math.PI;
                nodePositions[n.id] = {
                    x: cx + radius * Math.cos(angle),
                    y: cy + radius * Math.sin(angle)
                };
            }
        });

        // Draw Links
        data.edges.forEach(e => {
            const p1 = nodePositions[e.source] || { x: cx, y: cy };
            const p2 = nodePositions[e.target] || { x: cx, y: cy };
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", p1.x);
            line.setAttribute("y1", p1.y);
            line.setAttribute("x2", p2.x);
            line.setAttribute("y2", p2.y);
            line.setAttribute("stroke", "#4b5563");
            line.setAttribute("stroke-width", "1.5");
            line.setAttribute("stroke-dasharray", "4,2");
            svgEl.appendChild(line);
        });

        // Draw Nodes
        data.nodes.forEach(n => {
            const pos = nodePositions[n.id] || { x: cx, y: cy };
            const g = document.createElementNS("http://www.w3.org/2000/svg", "g");

            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("cx", pos.x);
            circle.setAttribute("cy", pos.y);
            circle.setAttribute("r", n.type === "Transaction" ? 14 : 11);
            circle.setAttribute("fill", getNodeColor(n.type));
            circle.setAttribute("stroke", "#ffffff");
            circle.setAttribute("stroke-width", "1.5");
            circle.style.cursor = "pointer";

            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", pos.x + 16);
            text.setAttribute("y", pos.y + 4);
            text.setAttribute("fill", "#e5e7eb");
            text.setAttribute("font-size", "10px");
            text.setAttribute("font-family", "Inter, sans-serif");
            text.setAttribute("font-weight", "500");
            text.textContent = n.label;

            g.appendChild(circle);
            g.appendChild(text);

            g.addEventListener("mouseover", (event) => {
                tooltipEl.style.display = "block";
                tooltipEl.style.left = (event.offsetX + 15) + "px";
                tooltipEl.style.top = (event.offsetY - 20) + "px";
                tooltipEl.innerHTML = `
                    <div style="font-weight:700;color:${getNodeColor(n.type)}">${n.type}: ${n.label}</div>
                    <div style="font-size:10px;margin-top:2px;color:#9ca3af;">Entity ID: ${n.id}</div>
                `;
            });
            g.addEventListener("mouseout", () => {
                tooltipEl.style.display = "none";
            });

            svgEl.appendChild(g);
        });

        graphContainer.appendChild(svgEl);
    }

    function getNodeColor(type) {
        switch (type) {
            case "Account": return "#3b82f6";
            case "Transaction": return "#ef4444";
            case "Device": return "#8b5cf6";
            case "IPAddress": return "#06b6d4";
            case "Customer": return "#10b981";
            default: return "#9ca3af";
        }
    }
});
