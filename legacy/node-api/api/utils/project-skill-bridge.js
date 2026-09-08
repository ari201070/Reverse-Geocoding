/**
 * Project Skill Bridge - Conecta Agent Skills (.agent/skills) con Project Skills (.skills/)
 * Fuente de verdad: .skills/ (7 skills del pipeline domain)
 */

import { loadSkill } from './skill-loader.js';
import fs from 'fs/promises';
import path from 'path';

const AGENT_SKILLS_DIR = '.agent/skills';
const PROJECT_SKILLS_DIR = '.skills';

const AGENT_SKILLS = [
  'ContextGeoIntegrator',
  'ExifDataSuite', 
  'GoogleCloudSuite',
  'BrowserOptimizationSuite',
  'MasterSyncSuite'
];

const PROJECT_SKILLS = [
  'capture',
  'extraction', 
  'processing',
  'analysis',
  'consensus',
  'persistence',
  'heritage'
];

/**
 * Carga todas las skills de ambas capas
 */
export async function loadAllSkills() {
  const agent = {};
  const project = {};

  // Cargar Agent Skills (.agent/skills/)
  for (const skillName of AGENT_SKILLS) {
    try {
      const content = await loadSkill(skillName);
      if (content) {
        agent[skillName] = content;
      }
    } catch (e) {
      console.warn(`[Bridge] Agent skill ${skillName} no encontrada:`, e.message);
    }
  }

  // Cargar Project Skills (.skills/)
  for (const skillName of PROJECT_SKILLS) {
    try {
      const content = await loadSkill(skillName);
      if (content) {
        project[skillName] = content;
      }
    } catch (e) {
      console.warn(`[Bridge] Project skill ${skillName} no encontrada:`, e.message);
    }
  }

  return { agent, project };
}

/**
 * Obtiene el prompt de una skill específica
 * @param {string} skillName - Nombre de la skill
 * @param {string} layer - 'agent' | 'project'
 */
export function getSkillPrompt(skillName, layer = 'project') {
  const normalizedName = layer === 'agent' 
    ? skillName  // Agent skills usan PascalCase
    : skillName.toLowerCase(); // Project skills usan lowercase
  
  const skills = layer === 'agent' ? AGENT_SKILLS : PROJECT_SKILLS;
  if (!skills.includes(normalizedName)) {
    return `## SKILL: ${skillName.toUpperCase()}\n[No encontrada en capa ${layer}]`;
  }

  return `## SKILL: ${skillName.toUpperCase()} (capa: ${layer})\n[Cargar con loadSkill('${normalizedName}')]`;
}

/**
 * Genera prompt combinado para inyección en LLM
 */
export async function getCombinedSkillPrompt(skillNames, layer = 'project') {
  const skills = await loadAllSkills();
  const source = layer === 'agent' ? skills.agent : skills.project;
  
  let prompt = `## SKILLS ACTIVADAS (capa: ${layer})\n\n`;
  
  for (const name of skillNames) {
    const content = source[name] || source[name.toLowerCase()];
    if (content) {
      prompt += `--- ${name.toUpperCase()} ---\n${content}\n\n`;
    } else {
      prompt += `--- ${name.toUpperCase()} ---\n[No disponible]\n\n`;
    }
  }
  
  return prompt;
}

/**
 * Obtiene todas las skills disponibles por capa
 */
export function getAvailableSkills() {
  return {
    agent: AGENT_SKILLS,
    project: PROJECT_SKILLS
  };
}

/**
 * Carga skills específicas para un pipeline stage
 */
export async function getPipelineSkills(stage) {
  const stageSkills = {
    capture: ['capture'],
    extraction: ['extraction'],
    processing: ['processing'],
    analysis: ['analysis'],
    consensus: ['consensus'],
    persistence: ['persistence'],
    heritage: ['heritage'],
    full: PROJECT_SKILLS
  };
  
  const names = stageSkills[stage] || PROJECT_SKILLS;
  return getCombinedSkillPrompt(names, 'project');
}

export default {
  loadAllSkills,
  getSkillPrompt,
  getCombinedSkillPrompt,
  getAvailableSkills,
  getPipelineSkills
};