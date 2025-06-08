document.querySelectorAll('nav a').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
  
<script>
  function increaseQty(id) {
    const input = document.getElementById(id);
    let current = parseInt(input.value);
    const max = parseInt(input.max);
    if (current < max) input.value = current + 1;
  }

  function decreaseQty(id) {
    const input = document.getElementById(id);
    let current = parseInt(input.value);
    const min = parseInt(input.min);
    if (current > min) input.value = current - 1;
  }
</script>
