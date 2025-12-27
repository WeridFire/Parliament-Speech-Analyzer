export function getCleanName(deputy) {
    if (!deputy) return '';
    return deputy.split('[')[0].trim();
}

export function getPartyFromDeputy(deputy) {
    if (!deputy) return 'Unknown Group';
    const match = deputy.match(/\[([^\]]+)\]/);
    return match ? match[1] : 'Unknown Group';
}
