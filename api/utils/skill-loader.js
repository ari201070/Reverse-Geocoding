import fs from 'fs/promises';
import path from 'path';

/**
 * SkillLoader loads the markdown files from the .skills directory
 * to be injected into the agent's context.
 */
export async function loadSkill(skillName) {
    try {
        const filePath = path.join(process.cwd(), '.skills', skillName.toLowerCase(), 'SKILL.md');
        const content = await fs.readFile(filePath, 'utf8');
        return content;
    } catch (e) {
        console.error(`[SkillLoader] Error loading skill ${skillName}:`, e.message);
        return null;
    }
}

export async function listAvailableSkills() {
    try {
        const skillsDir = path.join(process.cwd(), '.skills');
        const entries = await fs.readdir(skillsDir, { withFileTypes: true });
        return entries
            .filter(entry => entry.isDirectory())
            .map(entry => entry.name);
    } catch (e) {
        console.error(`[SkillLoader] Error listing skills:`, e.message);
        return [];
    }
}
