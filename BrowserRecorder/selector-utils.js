function getUniqueSelector(el) {
  if (!el) return null;

  const testId =
    el.getAttribute("data-testid") ||
    el.getAttribute("data-test") ||
    el.getAttribute("data-qa");

  if (testId)
    return `[data-testid="${testId}"]`;

  if (el.id)
    return `#${CSS.escape(el.id)}`;

  if (el.name)
    return `${el.tagName.toLowerCase()}[name="${el.name}"]`;

  let path = [];
  let node = el;

  while (node && node.nodeType === 1 && path.length < 5) {
    let selector = node.tagName.toLowerCase();

    if (node.className) {
      const cls = node.className.trim().split(/\s+/)[0];
      selector += "." + cls;
    }

    const siblings = Array.from(node.parentNode.children)
      .filter(n => n.tagName === node.tagName);

    if (siblings.length > 1) {
      const index = siblings.indexOf(node) + 1;
      selector += `:nth-of-type(${index})`;
    }

    path.unshift(selector);
    node = node.parentNode;
  }

  return path.join(" > ");
}

function getXPath(el) {
  if (el.id)
    return `//*[@id="${el.id}"]`;

  const parts = [];

  while (el && el.nodeType === 1) {
    let ix = 0;
    let sib = el.previousSibling;

    while (sib) {
      if (sib.nodeType === 1 && sib.tagName === el.tagName)
        ix++;
      sib = sib.previousSibling;
    }

    const tag = el.tagName.toLowerCase();
    parts.unshift(`${tag}[${ix + 1}]`);
    el = el.parentNode;
  }

  return "/" + parts.join("/");
}
