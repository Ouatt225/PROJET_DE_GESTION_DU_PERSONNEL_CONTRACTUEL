(function() {
    'use strict';

    function toggleDirections() {
        var roleField = document.getElementById('id_role');
        if (!roleField) return;

        // Trouver le fieldset des directions
        var directionsFieldset = null;
        var fieldsets = document.querySelectorAll('fieldset');
        fieldsets.forEach(function(fs) {
            var legend = fs.querySelector('h2, legend');
            if (legend && legend.textContent.indexOf('Directions') !== -1) {
                directionsFieldset = fs;
            }
        });

        // Aussi chercher la div du champ directions dans le formulaire de creation
        var directionsDiv = document.querySelector('.field-directions');

        if (roleField.value === 'manager') {
            if (directionsFieldset) {
                directionsFieldset.style.display = '';
                directionsFieldset.classList.remove('collapsed');
            }
            if (directionsDiv) directionsDiv.style.display = '';
        } else {
            if (directionsFieldset) directionsFieldset.style.display = 'none';
            if (directionsDiv) directionsDiv.style.display = 'none';
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        toggleDirections();

        var roleField = document.getElementById('id_role');
        if (roleField) {
            roleField.addEventListener('change', toggleDirections);
        }
    });
})();
