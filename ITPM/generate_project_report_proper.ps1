$ErrorActionPreference = 'Stop'

$template = "D:\college\projects\itpm\PROJECT TEMPLATE\ITPM Project Report-Template (1).doc"
$outDocx = "D:\college\projects\itpm\ITPM_Project_Report_AI_Leave_Management_Proper.docx"
$outDoc = "D:\college\projects\itpm\ITPM_Project_Report_AI_Leave_Management_Proper.doc"

$projectTitle = "AI-Enabled Employee Leave Management System"
$student1 = "<Student Name 1> (<RegNo.>)"
$student2 = "<Student Name 2> (<RegNo.>)"

$tocRows = @(
    @{ No = "1"; Date = "13-04-2026"; Name = "Requirement Analysis and Problem Definition"; Page = "4" },
    @{ No = "2"; Date = "13-04-2026"; Name = "Project Planning and Feasibility Study"; Page = "5" },
    @{ No = "3"; Date = "13-04-2026"; Name = "System Architecture and Database Design"; Page = "6" },
    @{ No = "4"; Date = "13-04-2026"; Name = "Authentication and Role-Based Access Control"; Page = "7" },
    @{ No = "5"; Date = "13-04-2026"; Name = "Leave Workflow and Policy Validation"; Page = "8" },
    @{ No = "6"; Date = "13-04-2026"; Name = "Dashboards, Reports, and Audit Tracking"; Page = "9" },
    @{ No = "7"; Date = "13-04-2026"; Name = "AI Smart Apply Helper and Leave Prediction"; Page = "10" },
    @{ No = "8"; Date = "13-04-2026"; Name = "Testing, Results, and Conclusion"; Page = "11" }
)

$sections = @(
    @{
        Title = "EXPERIMENT 1: REQUIREMENT ANALYSIS AND PROBLEM DEFINITION"
        Objective = "To study practical leave management issues and define complete software requirements."
        Theory = "Leave management in many organizations is often semi-manual, resulting in delayed approvals, poor visibility of balance, and inconsistent records. A centralized web platform with role separation and controlled workflow is required to solve these issues."
        Procedure = @(
            "Studied current pain points in manual and message-based leave processing.",
            "Identified stakeholders: employee, manager, and administrator.",
            "Mapped core workflows: request creation, review, approval/rejection, and reporting.",
            "Defined validation rules for date overlap, business days, notice period, and leave limits.",
            "Specified auditability and transparency as mandatory quality attributes."
        )
        Implementation = "The implemented system includes login, role-specific dashboards, leave apply/review pages, policy configuration, reporting, and activity logging. Requirements were mapped directly to routes, models, and templates in the project."
        Result = "A requirement-complete scope document was established and converted into working modules without scope ambiguity."
        Conclusion = "Clear requirements enabled consistent implementation and reduced redesign effort in later stages."
    },
    @{
        Title = "EXPERIMENT 2: PROJECT PLANNING AND FEASIBILITY STUDY"
        Objective = "To prepare a realistic execution plan and validate technical feasibility."
        Theory = "Project planning in software engineering ensures predictable development through phased execution, milestone tracking, and modular delivery. Feasibility analysis verifies whether chosen tools and architecture can satisfy functional expectations."
        Procedure = @(
            "Divided project into phases: setup, core workflow, analytics, and AI enhancement.",
            "Selected Python Flask for rapid web development and SQLAlchemy for ORM-based data access.",
            "Confirmed local development feasibility using SQLite and seeded sample data.",
            "Defined dependency set: Flask, Flask-SQLAlchemy, Flask-Login, and Werkzeug.",
            "Prepared reusable templates and centralized configuration strategy."
        )
        Implementation = "The project follows a single app entry with modular route blocks, separated data model definitions, and dedicated templates for auth, leave, admin, manager, and AI pages. Seed script initializes realistic users, policies, leave types, and balances."
        Result = "Planned milestones were technically feasible and aligned with available tools and timeline."
        Conclusion = "Proper planning enabled stable, incremental feature delivery with low rework."
    },
    @{
        Title = "EXPERIMENT 3: SYSTEM ARCHITECTURE AND DATABASE DESIGN"
        Objective = "To design scalable architecture and normalized schema for leave transactions."
        Theory = "A well-structured architecture separates business logic, view rendering, and persistence concerns. A relational schema with constraints ensures consistency for user identities, leave balances, and approvals."
        Procedure = @(
            "Defined core entities: User, LeaveType, LeaveBalance, LeaveRequest, LeavePolicy, AuditLog.",
            "Established one-to-many and reference relationships for manager-team and request-review flows.",
            "Added computed fields such as remaining_days for accurate leave tracking.",
            "Ensured uniqueness of username and email to avoid identity duplication.",
            "Created yearly leave balance management structure."
        )
        Implementation = "The data model is implemented in SQLAlchemy with explicit relationships and role-sensitive references. Leave requests include status, reviewed_by, and review_comment fields to support full lifecycle visibility. Policy table controls organization-level constraints."
        Result = "Database operations remained consistent across create, update, and reporting use cases."
        Conclusion = "The schema supports both current business rules and future extension needs."
    },
    @{
        Title = "EXPERIMENT 4: AUTHENTICATION AND ROLE-BASED ACCESS CONTROL"
        Objective = "To enforce secure access and role-appropriate operations for every user."
        Theory = "Authentication confirms user identity, while authorization controls permitted actions. Role-based access control reduces privilege misuse and protects sensitive administrative functions."
        Procedure = @(
            "Configured Flask-Login for session management and user loading.",
            "Implemented hashed password storage and credential verification.",
            "Created role_required decorator to gate route access.",
            "Mapped route permissions: employee, manager, admin.",
            "Handled invalid or inactive user login cases with proper feedback."
        )
        Implementation = "Login and logout routes are secured and audited. Employee-only endpoints include apply, precheck, and history. Manager endpoints handle request decisions for assigned team members. Admin endpoints control user, policy, leave-type, and reporting modules."
        Result = "Unauthorized route access was effectively blocked and role navigation stayed consistent."
        Conclusion = "RBAC implementation ensured process integrity and privacy across the system."
    },
    @{
        Title = "EXPERIMENT 5: LEAVE WORKFLOW AND POLICY VALIDATION"
        Objective = "To implement an end-to-end leave lifecycle with strict rule validation."
        Theory = "A robust leave workflow requires pre-submission checks, conflict handling, and post-approval balance updates. Policy enforcement must occur before request acceptance to reduce manager overhead."
        Procedure = @(
            "Built leave apply form with leave type, date range, and reason fields.",
            "Calculated business days by excluding weekends.",
            "Blocked overlapping approved or pending requests for same employee.",
            "Validated leave balance against requested business days.",
            "Applied policy checks for maximum consecutive days and minimum notice period.",
            "Implemented manager approve/reject actions with optional comments.",
            "Deducted leave balance only on approved requests."
        )
        Implementation = "The workflow is implemented through employee and manager route groups. A precheck API provides non-destructive guidance and returns status, issues, suggestions, and reason-quality analysis before final submission."
        Result = "Invalid requests were filtered early and approval processing became faster and more reliable."
        Conclusion = "Layered validations significantly improved operational correctness and user guidance."
    },
    @{
        Title = "EXPERIMENT 6: DASHBOARDS, REPORTS, AND AUDIT TRACKING"
        Objective = "To provide role-specific insights and governance-level visibility."
        Theory = "Dashboards convert transactional data into actionable metrics, while audit logs preserve accountability in administrative systems."
        Procedure = @(
            "Created admin cards for employee count, manager count, pending requests, and active leave status.",
            "Created manager cards for team size, pending approvals, and team-on-leave indicators.",
            "Created employee dashboard for leave balances and quick actions.",
            "Generated yearly report statistics for approved, rejected, and pending outcomes.",
            "Added leave-type and department-level request distribution summaries.",
            "Captured major events in audit log for traceability."
        )
        Implementation = "Report routes aggregate data using SQLAlchemy query filters and year-based extraction. Audit log entries are written for login/logout, pre-check usage, leave actions, and admin updates."
        Result = "Stakeholders obtained immediate visibility into workload, trends, and accountability records."
        Conclusion = "Reporting and auditing strengthened management decision quality and operational governance."
    },
    @{
        Title = "EXPERIMENT 7: AI SMART APPLY HELPER AND LEAVE PREDICTION"
        Objective = "To enhance decision support using deterministic rules and optional local AI."
        Theory = "AI-assisted systems should retain deterministic fallback logic to ensure reliability. Local model usage avoids mandatory paid APIs and supports privacy-aware deployments."
        Procedure = @(
            "Implemented rule-based reason quality analyzer with scoring and urgency detection.",
            "Integrated optional local Ollama model for richer reason suggestions.",
            "Normalized model outputs to controlled labels and capped recommendations.",
            "Added runtime status check for model availability and installed tags.",
            "Implemented leave pattern forecasting using historical approved leave features.",
            "Applied TTL in-memory cache for reason and prediction responses.",
            "Maintained graceful fallback when AI service is unavailable."
        )
        Implementation = "AI routes include reason preview, assistant view, and leave prediction dashboard for manager/admin. Hybrid merge logic keeps rule-based certainty dominant while incorporating optional model nuance."
        Result = "Reason quality feedback improved form clarity and planning pages provided forward-looking leave risk levels."
        Conclusion = "The AI layer added practical intelligence while preserving stable non-AI operation."
    },
    @{
        Title = "EXPERIMENT 8: TESTING, RESULTS, AND CONCLUSION"
        Objective = "To validate complete functionality and summarize project outcomes."
        Theory = "System quality is demonstrated through scenario-based functional testing, access-control checks, and negative-case validation."
        Procedure = @(
            "Tested authentication: valid login, invalid login, logout, inactive account behavior.",
            "Tested role boundaries by attempting protected routes from unauthorized roles.",
            "Tested leave apply validation: date order, weekend-only range, overlap, and low balance.",
            "Tested manager decisions and verified status transitions and comment persistence.",
            "Tested policy constraints and precheck suggestions for compliance.",
            "Tested dashboard metrics and report totals.",
            "Tested AI mode in both enabled and fallback conditions."
        )
        Implementation = "Seeded datasets were used to simulate real organization behavior and verify consistency of balances, approvals, and reports over multiple flows."
        Result = "The system met expected behavior across all critical scenarios and produced clear role-specific outputs."
        Conclusion = "The final product is a complete and practical leave management report implementation suitable for academic submission and real-world adaptation."
    }
)

$wdStory = 6
$wdPageBreak = 7
$wdAlignParagraphLeft = 0
$wdAlignParagraphCenter = 1
$wdReplaceAll = 2
$wdFindContinue = 1
$wdFormatDocumentDefault = 16
$wdFormatDocument97 = 0
$wdSeekMainDocument = 0
$wdLineStyleSingle = 1
$wdLineWidth050pt = 4
$wdColorAutomatic = 0

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

function Replace-AllText {
    param(
        [Parameter(Mandatory = $true)]$DocObj,
        [Parameter(Mandatory = $true)][string]$FindText,
        [Parameter(Mandatory = $true)][string]$ReplaceText
    )

    $range = $DocObj.Content
    $finder = $range.Find
    $finder.ClearFormatting()
    $finder.Replacement.ClearFormatting()
    $null = $finder.Execute($FindText, $false, $false, $false, $false, $false, $true, $wdFindContinue, $false, $ReplaceText, $wdReplaceAll)
}

function Add-Heading {
    param($SelectionObj, [string]$Text, [int]$Size = 13, [int]$Align = 0)
    $SelectionObj.ParagraphFormat.Alignment = $Align
    $SelectionObj.Font.Bold = 1
    $SelectionObj.Font.Size = $Size
    $SelectionObj.TypeText($Text)
    $SelectionObj.TypeParagraph()
}

function Add-LabelParagraph {
    param($SelectionObj, [string]$Label, [string]$Content)
    $SelectionObj.ParagraphFormat.Alignment = $wdAlignParagraphLeft
    $SelectionObj.Font.Size = 11
    $SelectionObj.Font.Bold = 1
    $SelectionObj.TypeText($Label + " ")
    $SelectionObj.Font.Bold = 0
    $SelectionObj.TypeText($Content)
    $SelectionObj.TypeParagraph()
}

function Add-PlainParagraph {
    param($SelectionObj, [string]$Content)
    $SelectionObj.ParagraphFormat.Alignment = $wdAlignParagraphLeft
    $SelectionObj.Font.Size = 11
    $SelectionObj.Font.Bold = 0
    $SelectionObj.TypeText($Content)
    $SelectionObj.TypeParagraph()
}

function Add-ExperimentOutline {
    param($SelectionObj)
    Add-Heading -SelectionObj $SelectionObj -Text "Experiment Outline" -Size 12 -Align $wdAlignParagraphLeft
    Add-PlainParagraph -SelectionObj $SelectionObj -Content "1. Objective"
    Add-PlainParagraph -SelectionObj $SelectionObj -Content "2. Theory"
    Add-PlainParagraph -SelectionObj $SelectionObj -Content "3. Procedure"
    Add-PlainParagraph -SelectionObj $SelectionObj -Content "4. Implementation in This Project"
    Add-PlainParagraph -SelectionObj $SelectionObj -Content "5. Result"
    Add-PlainParagraph -SelectionObj $SelectionObj -Content "6. Conclusion"
    Add-PlainParagraph -SelectionObj $SelectionObj -Content "7. Signature"
}

function Apply-DocumentPageOutline {
    param($DocObj)

    foreach ($section in $DocObj.Sections) {
        try {
            $section.Borders.Enable = 1
            foreach ($index in 1..4) {
                $border = $section.Borders.Item($index)
                $border.LineStyle = $wdLineStyleSingle
                $border.LineWidth = $wdLineWidth050pt
                $border.Color = $wdColorAutomatic
            }

            $section.Borders.DistanceFromTop = 18
            $section.Borders.DistanceFromLeft = 18
            $section.Borders.DistanceFromBottom = 18
            $section.Borders.DistanceFromRight = 18
        }
        catch {
            Write-Warning "Page outline could not be applied for one section: $($_.Exception.Message)"
        }
    }
}

try {
    $doc = $word.Documents.Open($template)
    $word.ActiveWindow.ActivePane.View.SeekView = $wdSeekMainDocument

    Replace-AllText -DocObj $doc -FindText "<NAME OF THE PROJECT>" -ReplaceText $projectTitle
    Replace-AllText -DocObj $doc -FindText "<Name of the Project>" -ReplaceText $projectTitle
    Replace-AllText -DocObj $doc -FindText "<Student Name><(RegNo.)>" -ReplaceText $student1
    Replace-AllText -DocObj $doc -FindText "<Student Name> <(RegNo.)>" -ReplaceText $student2

    $selection = $word.Selection
    $null = $selection.EndKey($wdStory)

    # Page 3: Table of Contents
    $selection.InsertBreak($wdPageBreak)
    Add-Heading -SelectionObj $selection -Text "TABLE OF CONTENTS" -Size 16 -Align $wdAlignParagraphCenter

    $rows = $tocRows.Count + 1
    $table = $doc.Tables.Add($selection.Range, $rows, 5)
    $table.Borders.Enable = 1

    $table.Cell(1, 1).Range.Text = "EXP. NO."
    $table.Cell(1, 2).Range.Text = "DATE"
    $table.Cell(1, 3).Range.Text = "EXPERIMENT NAME"
    $table.Cell(1, 4).Range.Text = "PAGE NO"
    $table.Cell(1, 5).Range.Text = "SIGNATURE"

    for ($c = 1; $c -le 5; $c++) {
        $table.Cell(1, $c).Range.Bold = 1
    }

    for ($i = 0; $i -lt $tocRows.Count; $i++) {
        $r = $i + 2
        $table.Cell($r, 1).Range.Text = $tocRows[$i].No
        $table.Cell($r, 2).Range.Text = $tocRows[$i].Date
        $table.Cell($r, 3).Range.Text = $tocRows[$i].Name
        $table.Cell($r, 4).Range.Text = $tocRows[$i].Page
        $table.Cell($r, 5).Range.Text = ""
    }

    $table.Columns.Item(1).PreferredWidth = 45
    $table.Columns.Item(2).PreferredWidth = 75
    $table.Columns.Item(3).PreferredWidth = 300
    $table.Columns.Item(4).PreferredWidth = 55
    $table.Columns.Item(5).PreferredWidth = 80

    $selection.SetRange($table.Range.End, $table.Range.End)

    foreach ($sec in $sections) {
        $selection.InsertBreak($wdPageBreak)

        Add-Heading -SelectionObj $selection -Text $sec.Title -Size 14 -Align $wdAlignParagraphLeft
        Add-ExperimentOutline -SelectionObj $selection
        Add-LabelParagraph -SelectionObj $selection -Label "Objective:" -Content $sec.Objective
        Add-LabelParagraph -SelectionObj $selection -Label "Theory:" -Content $sec.Theory

        Add-Heading -SelectionObj $selection -Text "Procedure" -Size 12 -Align $wdAlignParagraphLeft
        for ($i = 0; $i -lt $sec.Procedure.Count; $i++) {
            Add-PlainParagraph -SelectionObj $selection -Content (("{0}. {1}" -f ($i + 1), $sec.Procedure[$i]))
        }

        Add-LabelParagraph -SelectionObj $selection -Label "Implementation in This Project:" -Content $sec.Implementation
        Add-LabelParagraph -SelectionObj $selection -Label "Result:" -Content $sec.Result
        Add-LabelParagraph -SelectionObj $selection -Label "Conclusion:" -Content $sec.Conclusion
        Add-LabelParagraph -SelectionObj $selection -Label "Signature:" -Content "____________________"
    }

    Apply-DocumentPageOutline -DocObj $doc

    $doc.SaveAs([ref]$outDocx, [ref]$wdFormatDocumentDefault)
    $doc.SaveAs([ref]$outDoc, [ref]$wdFormatDocument97)
    $doc.Close()

    Write-Output "Created: $outDocx"
    Write-Output "Created: $outDoc"
}
finally {
    if ($word) {
        $word.Quit()
    }
}
